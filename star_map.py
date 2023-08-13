from random import choice, randrange, shuffle, randint
from constants import *
from location import Location, LocationType
from faction_type import FactionType, ai_empire_faction_types
from fleet import Fleet
from pygame.math import Vector2, clamp
from utility import phonetic_index, coin_flip, primary_system_names, secondary_system_names, prefix_system_names, d100, ai_empire_faction_post_labels, ai_empire_faction_pre_labels
from math import floor

# TODO: variable sized star maps, for when there is a zooming/scrolling map
#       and full-screen. 
class StarMap:
    def __init__(self, debug_mode):
        self.width = MAP_WIDTH_PX / LY
        self.height = MAP_HEIGHT_PX / LY
        self.locations = []
        self.deployed_fleets = []
        self.player_hw = None
        self.deployed_fleets = []
        self.faction_homeworlds = []
        self.faction_names = {}   
        self.faction_names[FactionType.EXOGALACTIC_INVASION] = "Invaders"
        self.num_stars = 0

        def generate_map(): 
            # partition the map into a spawning grid
            cells_wide = MAP_WIDTH_PX // PARTITION_GRID_SIDE
            cells_high = MAP_HEIGHT_PX // PARTITION_GRID_SIDE
            for x in range(cells_wide):
                for y in range(cells_high):
                    while True:
                        # pick a random point within the spawning grid cell
                        spawn_x = clamp(randrange(x * PARTITION_GRID_SIDE, x * PARTITION_GRID_SIDE + PARTITION_GRID_SIDE),
                                        MAP_BORDER_SPAWN_PADDING_PX, MAP_WIDTH_PX - MAP_BORDER_SPAWN_PADDING_PX)
                        spawn_y = clamp(randrange(y * PARTITION_GRID_SIDE, y * PARTITION_GRID_SIDE + PARTITION_GRID_SIDE),
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
                            self.locations.append(Location(name, pos, LocationType.STAR_SYSTEM, (x, y)))
                            self.num_stars += 1
                            break

        def place_player():
            # player starting world and fleets
            i = randrange(0, len(self.locations))
            self.locations[i].faction_type = FactionType.PLAYER
            self.locations[i].ships = PLAYER_STARTING_SHIPS
            if debug_mode:
                self.locations[i].ships = PLAYER_DEBUG_MODE_SHIPS
            self.locations[i].reenforce_chance_out_of_100 = DEFAULT_HW_REENFORCEMENT_CHANCE_OUT_OF_100
            self.locations[i].sensor_range = DEFAULT_HW_SENSOR_RANGE_LY
            self.player_hw = self.locations[i]
            self.faction_homeworlds.append(self.player_hw)
            self.faction_names[FactionType.PLAYER] = "Player"  

        def place_ai_empires():
            # AI Empire starting worlds and fleets
            shuffle(self.locations)
            generated = 0
            index = 0
            while generated < NUM_AI_EMPIRES:
                if self.locations[index].faction_type is None and self.locations[index].ly_to(self.player_hw.pos) > DEFAULT_HW_SENSOR_RANGE_LY:
                    self.locations[index].faction_type = ai_empire_faction_types[generated]
                    self.locations[index].ships = AI_EMPIRE_STARTING_SHIPS
                    self.locations[index].sensor_range = DEFAULT_HW_SENSOR_RANGE_LY
                    self.locations[index].reenforce_chance_out_of_100 = DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MAX
                    self.faction_homeworlds.append(self.locations[index])
                    generated += 1
                    if debug_mode:
                        self.locations[index].ships = AI_EMPIRE_DEBUG_MODE_SHIPS
                index += 1
            for loc in self.faction_homeworlds:
                if loc.faction_type != FactionType.PLAYER:
                    faction_name = "{}".format(loc.name)
                    if coin_flip() and len(faction_name) < AI_EMPIRE_FACTION_NAME_SIZE_CONSTRAINT:
                        faction_name = "{} {}".format(choice(ai_empire_faction_pre_labels), faction_name)
                    else:
                        faction_name = "{} {}".format(faction_name, choice(ai_empire_faction_post_labels))
                    self.faction_names[loc.faction_type] = faction_name

        def place_pirates():
            # Pirate starting worlds and fleets
            shuffle(self.locations)
            num_pirates = int(self.num_stars * PIRATE_DENSITY)
            generated = 0
            index = 0
            while generated < num_pirates:
                if self.locations[index].faction_type is None:
                    self.locations[index].faction_type = FactionType.PIRATES
                    self.locations[index].ships = randint(PIRATES_STARTING_SHIPS_MIN, PIRATES_STARTING_SHIPS_MAX)
                    if debug_mode:
                        self.locations[index].ships = PIRATE_DEBUG_MODE_SHIPS
                    generated += 1
                index += 1
            self.faction_names[FactionType.PIRATES] = "Pirates"

        def place_non_spacefaring():
            # non-space-faring worlds and fleets
            for loc in self.locations:
                if loc.faction_type is None:
                    loc.faction_type = FactionType.NON_SPACEFARING
                    loc.ships = randint(NON_SPACEFARING_STARTING_SHIPS_MIN, NON_SPACEFARING_STARTING_SHIPS_MAX)
                    if debug_mode:
                        loc.ships = NON_SPACEFARING_DEBUG_MODE_SHIPS
            self.faction_names[FactionType.NON_SPACEFARING] = "Local Forces"

        generate_map()
        place_player()
        place_ai_empires()
        place_pirates()
        place_non_spacefaring()

    def get_faction_homeworld(self, faction):
        for loc in self.faction_homeworlds:
            if loc.faction_type == faction:
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
        return len([i for i in filter(lambda x: x.faction_type == faction, self.deployed_fleets)])

    def name_a_fleet(self, faction):
        return "{} Fleet".format(phonetic_index(self.get_num_fleets_of_faction(faction)))

    def remove_fleet(self, fleet):
        if fleet in self.deployed_fleets:
            self.deployed_fleets.remove(fleet)

    def systems_in_range_of(self, loc):
        return [i for i in filter(lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY, self.locations)]

    # Returns closest friendly world for a fleet,
    # or None if there are none to be found
    def nearest_friendly_world_to(self, fleet):
        closest = None
        for loc in self.locations:
            if loc.faction_type == fleet.faction_type:
                if closest is None:
                    closest = loc
                else:
                    distance = Vector2(loc.pos).distance_to(Vector2(fleet.pos)) / LY
                    if distance < Vector2(closest.pos).distance_to(Vector2(fleet.pos)) / LY:
                        closest = loc
        return closest

    def deploy_fleet(self, source, dest, num_ships, ai_threat_check_flag=False, pre_waypoints=None):
        if num_ships < 1: 
            return
        if source.ly_to(dest.pos) > DEFAULT_FUEL_RANGE_LY:
            return
        if source == dest:
            return
        if source.ships - 1 >= num_ships:
            # Will prioritize veteran ships for deployment, until I implement a slider for that (TODO)
            total_vet_ships = source.get_num_vets()
            if num_ships <= total_vet_ships:
                vet = 100 
                diff = total_vet_ships - num_ships
                source.veterancy_out_of_100 = floor(diff / (source.ships - num_ships) * 100)
            else:  
                vet = floor(total_vet_ships / num_ships * 100)  
                source.veterancy_out_of_100 = 0 
            name = self.name_a_fleet(source.faction_type)
            fleet = Fleet(name, source.pos, source.faction_type, num_ships, dest, vet)
            fleet.ai_threat_check_flag = ai_threat_check_flag 
            if pre_waypoints is None:
                fleet.waypoints.append(dest)
            else:
                fleet.waypoints = pre_waypoints
            self.deployed_fleets.append(fleet)
            source.ships -= num_ships

    def nearest_vulnerable_world_to(self, fleet):
        neighbors = [i for i in filter(lambda x: x.ly_to(fleet.pos) <= DEFAULT_FUEL_RANGE_LY, self.locations)]
        weakest = None
        for loc in neighbors:
            if weakest is None:
                weakest = loc
            elif loc.ships < weakest.ships:
                weakest = loc
        return weakest

    def player_is_aware_of(self, pos):
        # can be seen by any fleet or location owned by the player
        owned_systems = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.locations)]
        for owned_loc in owned_systems:
            if owned_loc.ly_to(pos) <= owned_loc.sensor_range:
                return True
        owned_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.deployed_fleets)]
        for owned_fleet in owned_fleets:
            if owned_fleet.ly_to(pos) <= owned_fleet.sensor_range:
                return True
        return False

