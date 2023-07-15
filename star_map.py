from random import choice, randrange, shuffle
from constants import *
from location import Location, LocationType
from faction import Faction, ai_empire_factions
from pygame.math import Vector2, clamp
from utility import phonetic_index, coin_flip, primary_system_names, secondary_system_names, prefix_system_names, d100, ai_empire_faction_post_labels, ai_empire_faction_pre_labels


# Node class for advanced map building and AI behavior down the road
class Node:
    def __init__(self, loc, locations):
        self.value = loc
        self.children = []
        for other in locations:
            if other != loc and loc.ly_to(other.pos) <= DEFAULT_FUEL_RANGE_LY:
                self.children.append(other)


# TODO: variable sized star maps, for when there is a zooming/scrolling map
#       and full-screen. 
class StarMap:
    def __init__(self):
        self.width = MAP_WIDTH_PX / LY
        self.height = MAP_HEIGHT_PX / LY
        self.locations = []
        self.deployed_fleets = []
        self.player_hw = None
        self.deployed_fleets = []
        self.faction_homeworlds = []
        self.faction_names = {}
        self.num_stars = 0

        def generate_map():
            # partition the map into a spawning grid
            partition_grid_side = int((DEFAULT_FUEL_RANGE_LY * LY) // 2)
            cells_wide = MAP_WIDTH_PX // partition_grid_side
            cells_high = MAP_HEIGHT_PX // partition_grid_side
            for x in range(cells_wide):
                for y in range(cells_high):
                    while True:
                        # pick a random point within the spawning grid cell
                        spawn_x = clamp(randrange(x * partition_grid_side, x * partition_grid_side + partition_grid_side),
                                        MAP_BORDER_SPAWN_PADDING_PX, MAP_WIDTH_PX - MAP_BORDER_SPAWN_PADDING_PX)
                        spawn_y = clamp(randrange(y * partition_grid_side, y * partition_grid_side + partition_grid_side),
                                        MAP_BORDER_SPAWN_PADDING_PX, MAP_HEIGHT_PX - MAP_BORDER_SPAWN_PADDING_PX)
                        pos = (spawn_x, spawn_y)
                        # ensure picked spot isn't too close to any already-spawned locations
                        clear = True
                        for loc in self.locations:
                            if loc.ly_to(pos) <= STAR_MIN_DISTANCE_LY:
                                clear = False
                                break
                        if clear:
                            name = self.name_a_star_system()
                            self.locations.append(Location(name, pos, LocationType.STAR_SYSTEM))
                            self.num_stars += 1
                            break

        def place_player():
            # player starting world and fleets
            i = randrange(0, len(self.locations))
            self.locations[i].faction = Faction.PLAYER
            self.locations[i].ships = PLAYER_STARTING_SHIPS
            self.locations[i].reenforce_chance_out_of_100 = DEFAULT_HW_REENFORCEMENT_CHANCE_OUT_OF_100
            self.locations[i].sensor_range = DEFAULT_HW_SENSOR_RANGE_LY
            self.player_hw = self.locations[i]
            self.faction_names[Faction.PLAYER] = "Player"  # TODO: Better name for player

        def place_ai_empires():
            # AI Empire starting worlds and fleets
            shuffle(self.locations)
            generated = 0
            index = 0
            while generated < NUM_AI_EMPIRES:
                if self.locations[index].faction is None:
                    self.locations[index].faction = ai_empire_factions[generated]
                    self.locations[index].ships = AI_EMPIRE_STARTING_SHIPS
                    self.locations[index].sensor_range = DEFAULT_HW_SENSOR_RANGE_LY
                    self.locations[index].reenforce_chance_out_of_100 = DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MAX
                    self.faction_homeworlds.append(self.locations[index])
                    generated += 1
                index += 1
            for loc in self.faction_homeworlds:
                faction_name = "{}".format(loc.name)
                if coin_flip():
                    faction_name = "{} {}".format(choice(ai_empire_faction_pre_labels), faction_name)
                else:
                    faction_name = "{} {}".format(faction_name, choice(ai_empire_faction_post_labels))
                self.faction_names[loc.faction] = faction_name

        def place_pirates():
            # Pirate starting worlds and fleets
            shuffle(self.locations)
            num_pirates = self.num_stars // PERCENT_MAP_PIRATES
            generated = 0
            index = 0
            while generated < num_pirates:
                if self.locations[index].faction is None:
                    self.locations[index].faction = Faction.PIRATES
                    self.locations[index].ships = PIRATES_STARTING_SHIPS
                    generated += 1
                index += 1
            self.faction_names[Faction.PIRATES] = "Pirates"

        def place_non_spacefaring():
            # non-space-faring worlds and fleets
            for loc in self.locations:
                if loc.faction is None:
                    loc.faction = Faction.NON_SPACEFARING
                    loc.ships = NON_SPACEFARING_STARTING_SHIPS
            self.faction_names[Faction.NON_SPACEFARING] = "Local Forces"

        generate_map()
        place_player()
        place_ai_empires()
        place_pirates()
        place_non_spacefaring()

    def get_faction_homeworld(self, faction):
        for loc in self.faction_homeworlds:
            if loc.faction == faction:
                return loc
        return None

    def name_a_star_system(self):
        while True:
            name = choice(primary_system_names)
            if d100()[0] <= SYSTEM_PREFIX_CHANCE_OUT_OF_100:
                prefix = choice(prefix_system_names)
                name = "{} {}".format(prefix, name)
            if d100()[0] <= SYSTEM_SECONDARY_CHANCE_OUT_OF_100:
                suffix = choice(secondary_system_names)
                name = "{} {}".format(name, suffix)
            if name not in [i for i in map(lambda x: x.name, self.locations)]:
                return name

    def get_num_fleets_of_faction(self, faction):
        return len([i for i in filter(lambda x: x.faction == faction, self.deployed_fleets)])

    def name_a_fleet(self, faction):
        return "{} Fleet".format(phonetic_index(self.get_num_fleets_of_faction(faction)))

    def remove_fleet(self, fleet):
        if fleet in self.deployed_fleets:
            self.deployed_fleets.remove(fleet)

    # Returns closest friendly world for a fleet,
    # or None if there are none to be found
    def nearest_friendly_world_to(self, fleet):
        closest = None
        for loc in self.locations:
            if loc.faction == fleet.faction:
                if closest is None:
                    closest = loc
                else:
                    distance = Vector2(loc.pos).distance_to(Vector2(fleet.pos)) / LY
                    if distance < Vector2(closest.pos).distance_to(Vector2(fleet.pos)) / LY:
                        closest = loc
        return closest
