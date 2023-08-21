import pygame
from pygame.locals import *
from constants import *
from battle_sprite import BattleSprite
from tactical_battles import TacticalBattle
from star_map import StarMap
from location import LocationType, generate_starfield
from clickable import Clickable
from faction import Faction
from faction_type import FactionType, faction_type_to_color, ai_empire_faction_types
from fleet import Fleet
from console import ConsoleLog
from utility import d20, d100, phonetic_index, prefix_system_names, secondary_system_names, click_and_drag_rect, xthify
from pygame.math import Vector2
from random import shuffle, randint, choice
from math import ceil, floor
from personality import *
from battle_graph import BattleGraph

class Game:
    def __init__(self):
        self.debug_mode = False
        self.watch_mode = False
        self.routing_mode = False
        self.watch_timer = 0
        self.screen = pygame.display.get_surface()
        self.display_changed = False
        self.clock = pygame.time.Clock()
        self.running = True
        self.star_map = StarMap(self.debug_mode)
        self.hard_mode = False
        self.close_battles_toggle = False
        self.political_map_toggle = False
        self.drag_start = None
        self.drag_end = None
        self.multiple_locs_selected = []
        self.multiple_fleets_clicked = []
        self.clicked_fleets_index = 0
        self.remaining_factions = 6    
        self.coalition_triggered = False
        self.last_faction_buff = False 
        self.last_faction_buff_triggered = False  
        self.exogalactic_invasion_begun = False  
        self.exogalactic_invasion_countdown = EXOGALACTIC_INVASION_COUNTDOWN
        self.invasion_direction = None
        self.invasion_fleets_spawned = False
        self.invasion_waves_completed = 0
        self.turn_of_last_wave = 0
        self.console_scrolled_up_by = 0
        self.console_clickables = []
        self.displaying_battle_graph = None
        self.displaying_stats_graph = False
        self.displaying_fleets_graph = False
        self.coalition_trigger = COALITION_TRIGGER_PERCENT + randint(0, 5)

        self.battle_sprites = {}
        factions = [i for i in FactionType]
        for faction in factions: 
            self.battle_sprites[faction] = [BattleSprite(faction, DESTROYER_SHAPE_1), BattleSprite(faction, DESTROYER_SHAPE_2)]  

        self.ai_factions = []
        ai_types = [Water(), SnappingTurtle()]
        index = 1
        for fac in ai_empire_faction_types:
            if fac == FactionType.EXOGALACTIC_INVASION:
                ai_faction = Faction(fac, self, Haymaker())
                self.ai_factions.append(ai_faction)
            else:
                ai = choice(ai_types)
                ai = ai_types[index]
                index = (index + 1) % len(ai_types)  
                ai_faction = Faction(fac, self, ai)
                self.ai_factions.append(ai_faction)

        self.console = ConsoleLog()
        for msg in INTRO_STRINGS:
            self.console.push(msg)

        self.turn = 1
        self.mouse_last = pygame.mouse.get_pos()
        self.can_deploy_to = []
        self.eta_line_mode = False
        self.eta_line_target = None
        self.clearing_eta_line = False
        self.eta_sentinel = False
        self.selected_system = self.star_map.player_hw
        self.selected_fleet = None
        self.tactical_battle_ticker = 0
        self.tactical_battle_cooldown = TACTICAL_BATTLE_COOLDOWN
        self.tactical_battles = []
        self.tactical_battle_over = False
        self.skipping_tactical_battles = False

        # HUD animation stuff
        self.hud_ticker = 0

        # TODO: A common class for these two buttons
        self.deploy_mode = False
        self.deploy_amount = 0
        self.deploy_up_button = Clickable((MAP_WIDTH_PX, (HUD_FONT_SIZE + 1) * 4, 30, HUD_FONT_SIZE + 1))
        self.deploy_down_button = Clickable((MAP_WIDTH_PX + 30, (HUD_FONT_SIZE + 1) * 4, 30, HUD_FONT_SIZE + 1))
        self.deploy_button = Clickable(
            (MAP_WIDTH_PX + 60, (HUD_FONT_SIZE + 1) * 4, HUD_WIDTH_PX - 60, HUD_FONT_SIZE + 1))

        self.reenforce_mode = False
        self.reenforce_amount = 0
        self.player_reenforcement_pool = 0
        self.reenforce_up_button = Clickable((MAP_WIDTH_PX, (HUD_FONT_SIZE + 1) * 5, 30, HUD_FONT_SIZE + 1))
        self.reenforce_down_button = Clickable((MAP_WIDTH_PX + 30, (HUD_FONT_SIZE + 1) * 5, 30, HUD_FONT_SIZE + 1))
        self.reenforce_button = Clickable(
            (MAP_WIDTH_PX + 60, (HUD_FONT_SIZE + 1) * 5, HUD_WIDTH_PX - 60, HUD_FONT_SIZE + 1))

        self.incoming_fleets_overlay_mode = False  
        self.incoming_fleets_overlay_button = Clickable(
            (MAP_WIDTH_PX + 60, (HUD_FONT_SIZE + 1) * 10, HUD_WIDTH_PX, HUD_FONT_SIZE + 1))

        self.outgoing_fleets_overlay_mode = False  
        self.outgoing_fleets_overlay_button = Clickable(
            (MAP_WIDTH_PX + 60, (HUD_FONT_SIZE + 1) * 11, HUD_WIDTH_PX, HUD_FONT_SIZE + 1))

        self.system_strength_overlay_mode = True
        self.system_strength_overlay_button = Clickable(
            (MAP_WIDTH_PX + 60, (HUD_FONT_SIZE + 1) * 12, HUD_WIDTH_PX, HUD_FONT_SIZE + 1))

        self.reenforcement_chance_overlay_mode = False
        self.reenforcement_chance_overlay_button = Clickable(
            (MAP_WIDTH_PX + 60, (HUD_FONT_SIZE + 1) * 13, HUD_WIDTH_PX, HUD_FONT_SIZE + 1))

        self.sensor_range_overlay_mode = False
        self.sensor_range_overlay_button = Clickable(
            (MAP_WIDTH_PX + 60, (HUD_FONT_SIZE + 1) * 14, HUD_WIDTH_PX, HUD_FONT_SIZE + 1))

        self.end_turn_button = Clickable((MAP_WIDTH_PX, 0, HUD_WIDTH_PX / 2, HUD_FONT_SIZE + 1))
        self.turn_processing_mode = False
        self.game_over_mode = False
        self.all_pirates_destroyed = False
        self.all_ai_empires_destroyed = False
        self.victory_mode = False
        self.conquest_percent = 1

        self.battles_won = 0
        self.battles_lost = 0
        self.ships_lost = 0
        self.ships_destroyed = 0
        self.ships_over_time = []
        self.veteran_ships_over_time = []
        self.enemy_ships_over_time = []
        self.systems_over_time = []
        self.deployed_fleets_over_time = []
        self.decimated_systems_over_time = []
        self.ffa_stage_turn = 0
        self.coalition_stage_turn = False
        self.invader_stage_turn = False
        self.biggest_battle = 0
        # NOTE: more stats to come

    def game_loop(self):

        # TODO: a common "splash" class with more functionality
        def game_over_splash():
            # placeholder
            splash_rect = (MAP_WIDTH_PX // 4, MAP_HEIGHT_PX // 4, MAP_WIDTH_PX // 2, MAP_HEIGHT_PX // 2)
            pygame.draw.rect(self.screen, "black", splash_rect)
            pygame.draw.rect(self.screen, "red", splash_rect, 1)
            font = pygame.font.Font(FONT_PATH, GAME_OVER_SPLASH_FONT_SIZE)
            text = font.render("All of your star systems have been conquered...", True, "red")
            self.screen.blit(text,
                             (MAP_WIDTH_PX // 2 - text.get_width() // 2, MAP_HEIGHT_PX // 2 - text.get_height() // 2))

        # Toggles the running True/False variable based on whether the player has any planets left
        def game_over_check():
            # placeholder
            player_locs = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.locations)]
            if len(player_locs) == 0:
                self.console.push("Player has no worlds left!")
                self.game_over_mode = True
            else:
                self.game_over_mode = False

        def exogalactic_invader_countdown_check():
            if self.exogalactic_invasion_begun:
                if self.exogalactic_invasion_countdown > 0:
                    self.exogalactic_invasion_countdown -= 1
                elif self.invasion_waves_completed < EXOGALACTIC_INVASION_WAVE_LIMIT:
                    self.turn_of_last_wave = self.turn
                    self.invasion_fleets_spawned = True
                    self.exogalactic_invasion_countdown = randint(EXOGALACTIC_WAVE_DELAY_MIN, EXOGALACTIC_WAVE_DELAY_MAX)
                    self.invasion_waves_completed += 1
                    ship_count = 0
                    systems = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER or x.faction_type == FactionType.NON_SPACEFARING, self.star_map.locations)]
                    player_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.deployed_fleets)]
                    ship_count += sum(map(lambda x: x.ships, systems))
                    ship_count += sum(map(lambda x: x.ships, player_fleets))
                    existing_invader_systems = [i for i in filter(lambda x: x.faction_type == FactionType.EXOGALACTIC_INVASION, self.star_map.locations)]
                    existing_invader_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.EXOGALACTIC_INVASION, self.star_map.deployed_fleets)]
                    existing_invader_ship_count = sum(map(lambda x: x.ships, existing_invader_systems)) + sum(map(lambda x: x.ships, existing_invader_fleets))
                    invasion_targets = []
                    if self.invasion_direction == "top":
                        for system in self.star_map.locations:
                            if system.pos[1] <= INVASION_MARGIN_PX:
                                invasion_targets.append(system)
                    elif self.invasion_direction == "right":
                        for system in self.star_map.locations:
                            if system.pos[0] >= MAP_WIDTH_PX - INVASION_MARGIN_PX:
                                invasion_targets.append(system)
                    elif self.invasion_direction == "bottom":
                        for system in self.star_map.locations:
                            if system.pos[1] >= MAP_HEIGHT_PX - INVASION_MARGIN_PX:
                                invasion_targets.append(system)
                    elif self.invasion_direction == "left":
                        for system in self.star_map.locations:
                            if system.pos[0] <= INVASION_MARGIN_PX:
                                invasion_targets.append(system)
                    invader_ratio = EXOGALACTIC_INVASION_SIZE_RATIO
                    if self.hard_mode:
                        invader_ratio += .5
                    num_invaders = max(int(ship_count * invader_ratio) - existing_invader_ship_count, 1)
                    invader_fleets_size = max(num_invaders // len(invasion_targets), 1)
                    for target in invasion_targets:
                        name = self.star_map.name_a_fleet(FactionType.EXOGALACTIC_INVASION)
                        pos = None
                        if self.invasion_direction == "top":
                            pos = (target.pos[0], 0)
                        elif self.invasion_direction == "right":
                            pos = (MAP_WIDTH_PX, target.pos[1])
                        elif self.invasion_direction == "bottom":
                            pos = (target.pos[0], MAP_HEIGHT_PX)
                        elif self.invasion_direction == "left":
                            pos = (0, target.pos[1])
                        fleet = Fleet(name, pos, FactionType.EXOGALACTIC_INVASION, invader_fleets_size, target, 0)
                        self.star_map.deployed_fleets.append(fleet)

        def last_faction_buff_check():
            if self.last_faction_buff:
                faction_systems = [i for i in filter(lambda x: x.faction_type != FactionType.PLAYER and x.faction_type != FactionType.PIRATES and x.faction_type != FactionType.NON_SPACEFARING, self.star_map.locations)]
                num_faction_ships = sum(map(lambda x: x.ships, faction_systems))
                faction_fleets = [i for i in filter(lambda x: x.faction_type != FactionType.PLAYER and x.faction_type != FactionType.PIRATES and x.faction_type != FactionType.NON_SPACEFARING, self.star_map.deployed_fleets)]
                num_faction_ships += sum(map(lambda x: x.ships, faction_fleets))
                player_systems = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.locations)]
                player_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.deployed_fleets)]
                num_player_ships = sum(map(lambda x: x.ships, player_systems))
                num_player_ships += sum(map(lambda x: x.ships, player_fleets))
                if len(faction_systems) >= len(player_systems) or num_faction_ships >= num_player_ships:
                    self.last_faction_buff = False
                    if len(faction_systems) > 0:
                        name = self.ai_factions[0].name
                        self.console.push("{}'s production boost is complete.".format(name))
                        self.ai_factions[0].personality = SnappingTurtle()

        def activate_deploy_mode():
            if self.selected_system.faction_type == FactionType.PLAYER:
                self.console.push("DEPLOY MODE: Select target")
                self.deploy_mode = True
                self.display_changed = True
                if len(self.multiple_locs_selected) > 0:
                    self.can_deploy_to = []
                    for source in self.multiple_locs_selected:
                        for loc in self.star_map.locations:
                            if loc.ly_to(source.pos) <= DEFAULT_FUEL_RANGE_LY:
                                self.can_deploy_to.append(loc)
                else:
                    self.can_deploy_to = [i for i in filter(lambda x: x.ly_to(self.selected_system.pos) <= DEFAULT_FUEL_RANGE_LY, self.star_map.locations)]

        def victory_splash():
            splash_rect = (MAP_WIDTH_PX // 4, MAP_HEIGHT_PX // 4, MAP_WIDTH_PX // 2, MAP_HEIGHT_PX // 2)
            pygame.draw.rect(self.screen, "black", splash_rect)
            pygame.draw.rect(self.screen, "green", splash_rect, 1)
            font = pygame.font.Font(FONT_PATH, VICTORY_SPLASH_FONT_SIZE)
            y = splash_rect[1] + 1
            title_text = font.render("Victory! You have brought Sector 34 under your control!", True, "red")
            height = title_text.get_height() + 1
            self.screen.blit(title_text, (MAP_WIDTH_PX // 2 - title_text.get_width() // 2, y))
            y += 100
            battles_won_text = font.render("Won {} battles.".format(self.battles_won), True, "red")
            self.screen.blit(battles_won_text, (MAP_WIDTH_PX // 2 - battles_won_text.get_width() // 2, y + height))
            battles_lost_text = font.render("Lost {} battles.".format(self.battles_lost), True, "red")
            self.screen.blit(battles_lost_text, (MAP_WIDTH_PX // 2 - battles_lost_text.get_width() // 2, y + height * 2))
            ships_destroyed_text = font.render("Destroyed {} ships.".format(self.ships_destroyed), True, "red")
            self.screen.blit(ships_destroyed_text, (MAP_WIDTH_PX // 2 - ships_destroyed_text.get_width() // 2, y + height * 3))
            ships_lost_text = font.render("Lost {} ships.".format(self.ships_lost), True, "red")
            self.screen.blit(ships_lost_text, (MAP_WIDTH_PX // 2 - ships_lost_text.get_width() // 2, y + height * 4))
            bb_text = font.render("Biggest Battle: {} ships".format(self.biggest_battle), True, "red")
            self.screen.blit(bb_text, (MAP_WIDTH_PX // 2 - bb_text.get_width() // 2, y + height * 5))

        # Checks the victory conditions:
        def victory_check():
            num_pirate_systems = len(
                [i for i in filter(lambda x: x.faction_type == FactionType.PIRATES, self.star_map.locations)])
            ai_empire_systems = [i for i in filter(lambda x: x.faction_type in ai_empire_faction_types, self.star_map.locations)]
            num_ai_empire_systems = len(ai_empire_systems)
            num_player_systems = len(
                [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.locations)])
            conquest_percent = num_player_systems / self.star_map.num_stars * 100
            self.conquest_percent = conquest_percent
            alive_faction_list = []
            for system in ai_empire_systems:
                if system.faction_type not in alive_faction_list:
                    alive_faction_list.append(system.faction_type)
            self.remaining_factions = len(alive_faction_list)
            if num_pirate_systems == 0 and not self.all_pirates_destroyed:
                self.console.push("All Pirates in the sector have been brought under control...")
                self.all_pirates_destroyed = True
            if num_ai_empire_systems == 0 and not self.all_ai_empires_destroyed:
                empire_fleets = [i for i in filter(lambda x: x.faction_type in ai_empire_faction_types and x.faction_type != FactionType.PLAYER, self.star_map.deployed_fleets)]
                if len(empire_fleets) == 0:
                    self.console.push("All rival successors to the empire have been vanquished...")
                    self.all_ai_empires_destroyed = True
            if conquest_percent >= self.coalition_trigger and not self.coalition_triggered:
                self.coalition_triggered = True
                self.coalition_stage_turn = self.turn
                name = choice(["The Resistance", "The Coalition"])
                self.ai_factions[0].name = name
                self.ai_factions[0].personality = Water()
                for loc in self.star_map.locations:
                    if loc.faction_type != FactionType.PLAYER and loc.faction_type != FactionType.NON_SPACEFARING:
                        loc.faction_type = FactionType.AI_EMPIRE_1
                for fleet in self.star_map.deployed_fleets:
                    if fleet.faction_type != FactionType.PLAYER and fleet.faction_type != FactionType.NON_SPACEFARING:
                        fleet.faction_type = FactionType.AI_EMPIRE_1
                self.star_map.faction_names[FactionType.AI_EMPIRE_1] = name
                self.last_faction_buff = True  
                self.last_faction_buff_triggered = True
                self.console.push("{} throws all of their spare manpower into producing more ships...".format(name))
            if num_pirate_systems == 0 == num_ai_empire_systems and conquest_percent >= CONQUEST_PERCENT_FOR_VICTORY and not self.exogalactic_invasion_begun:
                empire_fleets = [i for i in filter(lambda x: x.faction_type in ai_empire_faction_types and x.faction_type != FactionType.PLAYER, self.star_map.deployed_fleets)]
                if len(empire_fleets) == 0:
                    for system in self.star_map.locations:
                        system.reenforce_chance_out_of_100 = LAST_FACTION_BUFF_PRODUCTION_BONUS
                    self.console.push("You have conquered Sector 34!")
                    self.invasion_direction = choice(["top", "right", "bottom", "left"])
                    self.console.push("Rumors of strange invaders from beyond the {} side of the map...".format(self.invasion_direction))
                    self.console.push("Prepare yourself... you have {} turns until the invasion!".format(EXOGALACTIC_INVASION_COUNTDOWN))
                    self.console.push("All systems in the sector start churning out ships to meet this new threat!".format(EXOGALACTIC_INVASION_COUNTDOWN))
                    self.exogalactic_invasion_begun = True
                    self.invader_stage_turn = self.turn
            if self.invasion_fleets_spawned:
                invader_systems = [i for i in filter(lambda x: x.faction_type == FactionType.EXOGALACTIC_INVASION, self.star_map.locations)]
                invader_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.EXOGALACTIC_INVASION, self.star_map.deployed_fleets)]
                if len(invader_systems) == 0 and len(invader_fleets) == 0:
                    self.console.push("You have defeated the exogalactic invasion!")
                    self.victory_mode = True

        # Returns true/false based on if point is within player's sensor range
        def player_can_see(pos):
            player_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.deployed_fleets)]
            player_locs = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.locations)]
            for fleet in player_fleets:
                if Vector2(fleet.pos).distance_to(Vector2(pos)) <= DEFAULT_FLEET_SENSOR_RANGE_LY * LY:
                    return True
            for loc in player_locs:
                if Vector2(loc.pos).distance_to(Vector2(pos)) <= loc.sensor_range * LY:
                    return True
            return False

        # Updates whether the player can see Fleets and Locations
        def update_fog_of_war():
            for fleet in self.star_map.deployed_fleets:
                if fleet.faction_type == FactionType.PLAYER or self.debug_mode:
                    fleet.in_sensor_view = True
                else:
                    fleet.in_sensor_view = player_can_see(fleet.pos)
            for loc in self.star_map.locations:
                if loc.faction_type == FactionType.PLAYER or self.debug_mode:
                    loc.in_sensor_view = True
                else:
                    loc.in_sensor_view = player_can_see(loc.pos)

        # Runs AI behavior 
        def run_ai_behavior():
            def pirate_system_routine(loc):
                # Pirates might attack nearby systems if they are weaker, regardless of faction
                # Each Pirate system operates independently. They can't reenforce each other,
                # and will attack each other. Conquered systems become new Pirate systems.
                # Pirate logic prefers the conservation of fleets over worlds, even more than
                # AI Empire faction logic.
                if not loc.under_threat(self.star_map.deployed_fleets):
                    locations_in_range = [i for i in filter(
                        lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY and loc.pos != x.pos,
                        self.star_map.locations)]
                    shuffle(locations_in_range)
                    for target in locations_in_range:
                        overmatched = target.ships * PIRATE_OVERMATCH_THRESHOLD < loc.ships
                        if overmatched and d100()[0] <= PIRATE_RAID_CHANCE_OUT_OF_100:
                            self.star_map.deploy_fleet(loc, target, loc.ships - 1)
                            break

            for loc in self.star_map.locations:
                if loc.faction_type == FactionType.PIRATES:
                    pirate_system_routine(loc)

            for fac in self.ai_factions:
                # AI Empire Factions make decisions on a higher level
                fac.run_behavior()

        # Moves any fleets
        def update_fleets():
            for fleet in self.star_map.deployed_fleets:
                fleet.move()

        # Each system has a random chance to spawn reenforcements.
        # Player reenforcements can go to a common pool, while all
        # AI reenforcements remain local.
        def spawn_reenforcements():
            for loc in self.star_map.locations:
                if loc.will_spawn_reenforcements(self.hard_mode, self.last_faction_buff):
                    if loc.faction_type == FactionType.PLAYER and d100()[0] <= DEFAULT_PLAYER_REENFORCEMENT_POOL_CHANCE_OUT_OF_100:
                        self.player_reenforcement_pool += 1
                    else:
                        vets = loc.get_num_vets() 
                        loc.ships += 1
                        loc.veterancy_out_of_100 = floor(vets / loc.ships * 100)

        # Finds any two fleets of opposing factions
        # at the same location, and resolves combats.
        # For now, there are no deep space interceptions
        # Friendly arrivals disembark at the destination
        def resolve_fleet_arrivals():

            def is_valid_reenforcement(fleet, loc):
                return fleet.arrived() and fleet.faction_type == loc.faction_type and fleet.faction_type != FactionType.PIRATES

            def is_valid_combat(fleet, loc):
                return fleet.arrived() and (fleet.faction_type == FactionType.PIRATES or fleet.faction_type != loc.faction_type)

            def is_last_stand(attackers, defenders):
                defender_faction = loc.faction_type
                defender_worlds = [i for i in filter(lambda x: x.faction_type == defender_faction, self.star_map.locations)]
                last_world = len(defender_worlds) == 1
                return (attackers > defenders and d100()[0] <= LAST_STAND_CHANCE_OUT_OF_100) or last_world

            def is_charge(attackers, defenders):
                nearby_friendly_worlds = [i for i in filter(lambda x: x.faction_type == fleet.faction_type, self.star_map.systems_in_range_of(loc))]
                nowhere_to_flee = len(nearby_friendly_worlds) == 0
                return (defenders > attackers and d100()[0] <= CHARGE_CHANCE_OUT_OF_100) or nowhere_to_flee

            def is_brilliancy():
                return d100()[0] <= BRILLIANCY_CHANCE_OUT_OF_100

            def battle_over(attackers, defenders):
                return attackers <= 0 or defenders <= 0

            def get_outnumber_margin(more, less): 
                outnumber_margin = 0             
                count = 1
                while True: 
                    if more >= less * BASE_OUTNUMBER_MARGIN * count:
                        outnumber_margin += 1
                        count += 1
                    else:
                        break
                return outnumber_margin

            def fleet_widths(attackers, defenders):
                nonlocal get_outnumber_margin
                default_width = min((attackers + defenders) // FLEET_WIDTH_DIVISOR, FLEET_WIDTH_MAX)
                if default_width < DEFAULT_FLEET_WIDTH:
                    default_width = DEFAULT_FLEET_WIDTH
                if attackers > defenders: 
                    outnumber_margin = get_outnumber_margin(attackers, defenders)
                    attackers_width = default_width + outnumber_margin
                    defenders_width = default_width
                elif attackers < defenders:
                    outnumber_margin = get_outnumber_margin(defenders, attackers)
                    attackers_width = default_width
                    defenders_width = default_width + outnumber_margin
                else:
                    attackers_width = default_width
                    defenders_width = default_width
                if attackers < DEFAULT_FLEET_WIDTH:
                    attackers_width = attackers
                if defenders < DEFAULT_FLEET_WIDTH:
                    defenders_width = defenders
                return (attackers_width, defenders_width)

            def might_retreat(rounds, attackers, defenders, charge):
                return rounds > 1 and attackers > 0 and not charge and attackers < defenders

            def will_retreat(attackers, defenders):
                nonlocal get_outnumber_margin
                outnumber_margin = get_outnumber_margin(defenders, attackers)
                retreat_chance_out_of_100 = DEFAULT_RETREAT_CHANCE_OUT_OF_100 * outnumber_margin
                if retreat_chance_out_of_100 > DEFAULT_RETREAT_CHANCE_HARD_CAP:
                    retreat_chance_out_of_100 = DEFAULT_RETREAT_CHANCE_HARD_CAP
                if d100()[0] <= retreat_chance_out_of_100:
                    return True
                return False

            def can_retreat():
                nearest_place_to_flee = self.star_map.nearest_friendly_world_to(fleet)
                if nearest_place_to_flee is not None:
                    if nearest_place_to_flee.ly_to(fleet.pos) <= DEFAULT_FUEL_RANGE_LY:
                        return True
                return False

            def is_retreat(rounds, attackers, defenders, charge): 
                return might_retreat(rounds, attackers, defenders, charge) and will_retreat(attackers, defenders) and can_retreat()

            def push_battle_results_to_console(loc, fleet_name, attackers_won, defenders_won, attacker_faction, defender_faction, retreat, attackers_losses, defenders_losses, rounds, graph):
                attacker_name = self.star_map.faction_names[attacker_faction]
                if not (attacker_faction == FactionType.PLAYER or defender_faction == FactionType.PLAYER):
                    return 
                defensive_total_victory = defenders_won and not retreat
                if attackers_won:
                    self.console.push("{} of {} conquered {} (losses: {} atk / {} def, {} rounds)".format(fleet_name, attacker_name, loc.name, attackers_losses, defenders_losses, rounds), graph)
                elif defensive_total_victory:
                    self.console.push("defenders of {} destroyed {} from {} (losses: {} atk / {} def; {} rounds)".format(loc.name, fleet_name, attacker_name, attackers_losses, defenders_losses, rounds), graph)
                else:
                    self.console.push("defenders of {} forced {} from {} to retreat (losses: {} atk / {} def; {} rounds)".format(loc.name, fleet_name, attacker_name, attackers_losses, defenders_losses, rounds), graph)

            def effects_of_battle_on_game_state(attackers, defenders, tactical_battle, loc, fleet, retreating, attackers_losses, defenders_losses, rounds, graph):  
                if loc.ships + fleet.ships > self.biggest_battle:
                    self.biggest_battle = loc.ships + fleet.ships
                attacker_faction = fleet.faction_type
                defender_faction = loc.faction_type
                attacker_name = fleet.name
                attackers_won = False
                defenders_won = False
                retreating = retreating
                if attackers > 0 >= defenders: 
                    # Attackers won:
                    tactical_battle.winner = attacker_faction
                    loc.faction_type = fleet.faction_type
                    loc.ships = attackers
                    if fleet == self.selected_fleet:
                        self.selected_fleet = None 
                    fleet.to_be_removed = True
                    attackers_won = True
                    if attacker_faction == FactionType.PIRATES:
                        self.all_pirates_destroyed = False
                    if attacker_faction == FactionType.EXOGALACTIC_INVASION:
                        loc.decimate() 
                elif attackers <= 0:
                    # defenders won without a retreat
                    tactical_battle.winner = defender_faction
                    loc.ships = defenders
                    if fleet == self.selected_fleet:
                        self.selected_fleet = None
                    fleet.to_be_removed = True
                    defenders_won = True
                    if defender_faction == FactionType.PIRATES:
                        self.all_pirates_destroyed = False

                # Handle retreats
                if retreating: 
                    tactical_battle.winner = defender_faction
                    loc.ships = defenders
                    fleet.ships = attackers
                    retreating_to = self.star_map.nearest_friendly_world_to(fleet)
                    if fleet.faction_type == FactionType.PIRATES:
                        retreating_to = self.star_map.nearest_vulnerable_world_to(fleet)
                    if retreating_to is None:
                        fleet.to_be_removed = True
                    else:
                        fleet.destination = retreating_to
                        fleet.waypoints = [fleet.destination]

                # Handle output if player involved
                push_battle_results_to_console(loc, attacker_name, attackers_won, defenders_won, attacker_faction, defender_faction, retreating, attackers_losses, defenders_losses, rounds, graph)

                # Handle player-specific effects                
                if attacker_faction == FactionType.PLAYER or defender_faction == FactionType.PLAYER:
                    if self.close_battles_toggle:
                        if tactical_battle.is_close_battle():
                            self.tactical_battles.append(tactical_battle)
                    else:
                        self.tactical_battles.append(tactical_battle)
                    if attackers_won and attacker_faction == FactionType.PLAYER:
                        self.battles_won += 1
                        self.ships_destroyed += defenders_losses
                        self.ships_lost += attackers_losses
                    else:
                        self.battles_lost += 1
                        self.ships_destroyed += defenders_losses
                        self.ships_lost += attackers_losses

                fleet.veterancy_out_of_100 = 100
                loc.veterancy_out_of_100 = 100

            def waypoint_handler(fleet):
                if fleet.destination in fleet.waypoints:
                    fleet.waypoints.remove(fleet.destination)  
                if len(fleet.waypoints) > 0:
                    fleet.destination = fleet.waypoints[0]
                    return True
                return False

            def handle_reenforcement(fleet, loc): 
                if not waypoint_handler(fleet): 
                    loc.mix_fleet(fleet)
                    if fleet is self.selected_fleet:
                        self.selected_fleet = None
                    fleet.to_be_removed = True

            def handle_combat(fleet, loc):
                graph = BattleGraph(fleet.ships, loc.ships)
                # A combat begins
                attackers = fleet.ships
                attacker_faction = fleet.faction_type
                defenders = loc.ships
                defender_faction = loc.faction_type
                fighting = True
                retreating = False
                attackers_losses = 0
                defenders_losses = 0
                rounds = 1
                tactical_battle = TacticalBattle(self.battle_sprites, fleet, loc, attacker_faction, defender_faction, attackers, defenders)
                tactical_battle.battle_number = loc.battles
                tactical_battle.starfield = loc.starfield
                last_stand = is_last_stand(attackers, defenders)
                if last_stand:
                    tactical_battle.last_stand = True 
                charge = is_charge(attackers, defenders)
                if charge:
                    tactical_battle.charge = True
                if charge and d100()[0] <= LAST_STAND_CHANCE_OUT_OF_100:
                    last_stand = True
                    tactical_battle.last_stand = True
                graph.charge = charge
                graph.last_stand = last_stand
                graph.xp_bonuses = {"attacker": fleet.get_veterancy_roll_bonus(), "defender": loc.get_veterancy_roll_bonus()}
                graph_colors = {"attacker": "red", "defender": "red"}
                if fleet.faction_type == FactionType.PLAYER:
                    graph_colors["attacker"] = "green"
                else:
                    graph_colors["defender"] = "green"
                graph.colors = graph_colors
                graph.battle_name = "{} battle of {}".format(xthify(loc.battles + 1), loc.name)
                graph.battle_turn = self.turn
                while fighting: 
                    brilliancies = {"attacker": False, "defender": False}
                    attacker_round_losses = 0
                    defender_round_losses = 0
                    # Attacker Bonuses
                    attacker_bonus = 0
                    if charge:
                        attacker_bonus += CHARGE_D20_BONUS
                    if is_brilliancy():
                        attacker_bonus += BRILLIANCY_BONUS
                        brilliancies["attacker"] = True
                    # Defender Bonuses
                    defender_bonus = 0
                    if last_stand:
                        defender_bonus += LAST_STAND_D20_BONUS
                    if is_brilliancy():
                        defender_bonus += BRILLIANCY_BONUS
                        brilliancies["defender"] = True
                    tactical_battle.brilliancies.append(brilliancies)
                    graph.brilliancies_by_side_per_round.append(brilliancies)
                    # Veterancy bonuses:
                    tactical_battle.attacker_vet_bonus = fleet.get_veterancy_roll_bonus()
                    attacker_bonus += tactical_battle.attacker_vet_bonus
                    tactical_battle.defender_vet_bonus = loc.get_veterancy_roll_bonus() 
                    defender_bonus += tactical_battle.defender_vet_bonus
                    # end of battle check
                    if battle_over(attackers, defenders):
                        break
                    # calculate fleet widths and bonuses
                    outnumber_die = {"attacker": 0, "defender": 0}
                    attackers_width, defenders_width = fleet_widths(attackers, defenders)
                    measure_width = min(attackers_width, defenders_width)
                    graph.fleet_width_per_round.append(measure_width)
                    if attackers_width > measure_width:
                        outnumber_die["attacker"] = attackers_width - measure_width
                    elif defenders_width > measure_width:
                        outnumber_die["defender"] = defenders_width - measure_width
                    tactical_battle.outnumber_die.append(outnumber_die)
                    graph.outnumber_dice_by_side_per_round.append(outnumber_die)

                    # roll for attackers and defenders
                    attackers_roll = d20(num_dice=attackers_width, bonus=attacker_bonus)
                    defenders_roll = d20(num_dice=defenders_width, bonus=defender_bonus)
                    rolls = {"attacker_rolls": [], "defender_rolls": []} 
                    for die in range(measure_width): 
                        # NOTE: Includes bonuses in roll dialogue result
                        rolls["attacker_rolls"].append(attackers_roll[die])
                        rolls["defender_rolls"].append(defenders_roll[die])
                        if attackers_roll[die] > defenders_roll[die]:
                            defenders -= 1
                            defenders_losses += 1
                            defender_round_losses += 1
                        else:  # defenders win ties for now
                            attackers -= 1
                            attackers_losses += 1
                            attacker_round_losses += 1
                    tactical_battle.rolls.append(rolls) 

                    # Handle potential retreats
                    if is_retreat(rounds, attackers, defenders, charge):
                        fighting = False
                        retreating = True
                        tactical_battle.retreat = True

                    tactical_battle.rounds.append({"attacker_losses": attacker_round_losses, "defender_losses": defender_round_losses})
                    graph.ships_by_side_per_round.append({"attacker": attackers, "defender": defenders})
                        
                    rounds += 1
    

                # Handle the effects of the battle
                effects_of_battle_on_game_state(attackers, defenders, tactical_battle, loc, fleet, retreating, attackers_losses, defenders_losses, rounds, graph)

            for fleet in self.star_map.deployed_fleets: 
                loc = fleet.destination
                if is_valid_reenforcement(fleet, loc): 
                    handle_reenforcement(fleet, loc)
                elif is_valid_combat(fleet, loc): 
                    handle_combat(fleet, loc)
                    if loc.faction_type == FactionType.PLAYER or fleet.faction_type == FactionType.PLAYER:
                        loc.battles += 1

        def remove_fleets():
            hits = False
            while True:
                hits = False
                for fleet in self.star_map.deployed_fleets:
                    if fleet.to_be_removed:
                        hits = True
                        self.star_map.remove_fleet(fleet)
                        break
                if not hits:
                    break

        def check_end_turn_clicks(pos):  
            if self.end_turn_button.clicked(pos):
                self.turn_processing_mode = True
                self.display_changed = True

        # Check if any locations have been clicked on:
        def check_location_clicks(pos): 
            ctrl = pygame.key.get_pressed()[K_LCTRL] or pygame.key.get_pressed()[K_RCTRL]
            shift = pygame.key.get_pressed()[K_LSHIFT] or pygame.key.get_pressed()[K_RSHIFT]
            for loc in self.star_map.locations: 
                if loc.clicked(pos):
                    # drag-selected deploy
                    if self.deploy_mode and len(self.multiple_locs_selected) > 1:
                        valid_deployments = []
                        for source in self.multiple_locs_selected:
                            distance = Vector2(loc.pos).distance_to(source.pos) / LY
                            if distance <= DEFAULT_FUEL_RANGE_LY and source.ships > 1:
                                valid_deployments.append(source)
                        if len(valid_deployments) > 0:
                            num_ships = sum([i for i in map(lambda x: x.ships - 1, valid_deployments)])
                            self.console.push(
                                "Deploying {} ships to {}".format(num_ships, loc.name))
                            for source in valid_deployments: # TODO: Some pop-ups which allow +/- on each selected source
                                self.star_map.deploy_fleet(source, loc, source.ships - 1)
                            self.deploy_mode = False
                            self.display_changed = True
                            self.multiple_locs_selected = []
                    # waypoint handling
                    elif ctrl and self.selected_fleet is not None:
                        distance = Vector2(loc.pos).distance_to(self.selected_fleet.waypoints[-1].pos) / LY
                        self.selected_fleet.add_waypoint(loc)  
                    elif shift and self.selected_fleet is not None:
                        self.selected_fleet.remove_waypoint(loc) 
                    # single system deploy
                    elif self.deploy_mode and self.deploy_amount > 0:
                        if not loc.pos == self.selected_system.pos: 
                            distance = Vector2(loc.pos).distance_to(self.selected_system.pos) / LY
                            if distance <= DEFAULT_FUEL_RANGE_LY:
                                self.console.push(
                                    "Deploying fleet of {} ships to {}".format(self.deploy_amount, loc.name))
                                self.star_map.deploy_fleet(self.selected_system, loc, self.deploy_amount)
                                self.selected_fleet = self.star_map.deployed_fleets[-1] # test
                                self.deploy_mode = False
                                self.deploy_amount = 0
                                self.display_changed = True
                                break
                            else:
                                self.console.push("Destination out of fuel range!")
                                self.display_changed = True

                    if self.reenforce_mode:
                        if loc.faction_type == FactionType.PLAYER:
                            self.console.push("Reenforcing {} with {} ships.".format(loc.name, self.reenforce_amount))
                            self.player_reenforcement_pool -= self.reenforce_amount
                            vets = loc.get_num_vets()
                            loc.ships += self.reenforce_amount
                            loc.veterancy_out_of_100 = floor(vets / loc.ships * 100)
                            self.reenforce_amount = 0
                            self.reenforce_mode = False
                            self.display_changed = True
                    elif loc.pos != self.selected_system.pos and (player_can_see(loc.pos) or self.debug_mode):
                        self.selected_system = loc
                        self.deploy_amount = 0
                        self.display_changed = True
                        self.multiple_locs_selected = []
                        break

        def check_reenforce_button_clicks(pos, shift, ctrl):
            if self.reenforce_button.clicked(pos) and self.reenforce_amount > 0:
                self.console.push("REENFORCE MODE: Select target")
                self.reenforce_mode = True
                self.display_changed = True
            elif self.reenforce_up_button.clicked(pos): 
                if not (shift or ctrl) and self.reenforce_amount <= self.player_reenforcement_pool: 
                    self.reenforce_amount += 1
                    self.display_changed = True
                elif shift and self.reenforce_amount + 10 <= self.player_reenforcement_pool:
                    self.reenforce_amount += 10
                    self.display_changed = True
                elif ctrl and self.player_reenforcement_pool > 0:
                    self.reenforce_amount = self.player_reenforcement_pool
                    self.display_changed = True
            elif self.reenforce_down_button.clicked(pos):
                if not (shift or ctrl) and self.reenforce_amount > 0:
                    self.reenforce_amount -= 1
                    self.display_changed = True
                elif shift and self.reenforce_amount >= 10:
                    self.reenforce_amount -= 10
                    self.display_changed = True
                elif ctrl and self.reenforce_amount > 0:
                    self.reenforce_amount = 0
                    self.display_changed = True

        def check_console_clickables(pos):
            for clickable in self.console_clickables:
                if clickable.clicked(pos): 
                    self.displaying_battle_graph = clickable.attachment 

        def check_deploy_button_clicks(pos, shift, ctrl):
            if self.deploy_button.clicked(pos):
                activate_deploy_mode() 

            elif self.deploy_up_button.clicked(pos) and self.selected_system.faction_type == FactionType.PLAYER:
                if not (shift or ctrl) and self.deploy_amount < self.selected_system.ships - 1:
                    self.deploy_amount += 1
                    self.display_changed = True
                elif shift and self.deploy_amount + 10 <= self.selected_system.ships - 1:
                    self.deploy_amount += 10
                    self.display_changed = True
                elif ctrl and self.selected_system.ships > 0:
                    self.deploy_amount = self.selected_system.ships - 1
                    self.display_changed = True
            elif self.deploy_down_button.clicked(pos) and self.selected_system.faction_type == FactionType.PLAYER:
                if not (shift or ctrl) and self.deploy_amount > 0:
                    self.deploy_amount -= 1
                    self.display_changed = True
                elif shift and self.deploy_amount - 10 >= 0:
                    self.deploy_amount -= 10
                    self.display_changed = True
                elif ctrl and self.deploy_amount > 0:
                    self.deploy_amount = 0
                    self.display_changed = True

        # Checks for clicks on any deployed fleets:
        def check_fleet_clicks(pos):
            ctrl = pygame.key.get_pressed()[K_LCTRL] or pygame.key.get_pressed()[K_RCTRL]
            shift = pygame.key.get_pressed()[K_LSHIFT] or pygame.key.get_pressed()[K_RSHIFT]
            if ctrl or shift:
                return
            self.clicked_fleets_index = 0
            clicked_fleets = []
            for fleet in self.star_map.deployed_fleets:
                if fleet.clicked(pos) and (player_can_see(pos) or self.debug_mode):
                    clicked_fleets.append(fleet)
            if len(clicked_fleets) > 0:
                self.selected_fleet = clicked_fleets[0]
                self.multiple_fleets_clicked = clicked_fleets 
                self.display_changed = True

        def draw_eta_line(start, end):  
            # Display ETA line
            if start.pos != end.pos:
                color = COLOR_SENSOR
                pygame.draw.line(self.screen, color, start.pos, end.pos, FLEET_ETA_LINE_WIDTH)
                eta = start.get_eta_to(end.pos)
                text = "{} TURNS".format(eta)
                font = pygame.font.Font(FONT_PATH, ETA_LINE_FONT_SIZE)
                surface = font.render(text, True, COLOR_FUEL_RANGE, "black")
                pos = (start.pos[0], start.pos[1])
                self.screen.blit(surface, pos)

        def draw_incoming_fleets_overlay(): 
            for fleet in self.star_map.deployed_fleets:
                if fleet.faction_type != FactionType.PLAYER and self.star_map.player_is_aware_of(fleet.pos):
                    if fleet.destination.faction_type == FactionType.PLAYER:
                        color = faction_type_to_color(fleet.faction_type)
                        font = pygame.font.Font(FONT_PATH, FLEET_OVERLAY_FONT_SIZE)
                        surface = font.render("{} (eta: {})".format(fleet.ships, fleet.get_eta()), True, color, "black")
                        pygame.draw.line(self.screen, color, fleet.pos, fleet.destination.pos, FLEET_ETA_LINE_WIDTH)
                        pos = (fleet.pos[0] - surface.get_width() / 2, fleet.pos[1] - surface.get_height() / 2)
                        self.screen.blit(surface, pos)

        def draw_outgoing_fleets_overlay():  
            for fleet in self.star_map.deployed_fleets:
                if fleet.faction_type == FactionType.PLAYER:
                    color = "green"
                    font = pygame.font.Font(FONT_PATH, FLEET_OVERLAY_FONT_SIZE)
                    surface = font.render("{} (eta: {})".format(fleet.ships, fleet.get_eta()), True, color, "black")
                    pygame.draw.line(self.screen, color, fleet.pos, fleet.destination.pos, FLEET_ETA_LINE_WIDTH)
                    pos = (fleet.pos[0] - surface.get_width() / 2, fleet.pos[1] - surface.get_height() / 2)
                    self.screen.blit(surface, pos)

        def draw_processing_blurb(): 
            font = pygame.font.Font(FONT_PATH, TACTICAL_MODE_FONT_SIZE)
            text = font.render("thinking...", True, "green", "black")
            x = MAP_WIDTH_PX / 2 - text.get_width() / 2
            y = MAP_HEIGHT_PX - text.get_height() - 10
            self.screen.blit(text, (x, y))
            pygame.display.flip()

        # Draws the map, hud, and bottom console to the screen
        def draw_display():
            update_fog_of_war()

            def draw_map():
                map_surface = pygame.Surface((MAP_WIDTH_PX, MAP_HEIGHT_PX))
                # fog of war
                map_surface.fill(COLOR_FOG)
                for loc in self.star_map.locations:
                    if loc.faction_type == FactionType.PLAYER or self.debug_mode:
                        radius = (loc.sensor_range * LY)
                        pygame.draw.circle(map_surface, "black", loc.pos, radius)
                for fleet in self.star_map.deployed_fleets:
                    if fleet.faction_type == FactionType.PLAYER or self.debug_mode:
                        radius = (DEFAULT_FLEET_SENSOR_RANGE_LY * LY)
                        pygame.draw.circle(map_surface, "black", fleet.pos, radius)

                # Draw the political map, if toggled
                if self.political_map_toggle:
                    cells_wide = MAP_WIDTH_PX // PARTITION_GRID_SIDE
                    cells_high = MAP_HEIGHT_PX // PARTITION_GRID_SIDE
                    for x in range(cells_wide):
                        for y in range(cells_high):
                            rect = (x * PARTITION_GRID_SIDE, y * PARTITION_GRID_SIDE, PARTITION_GRID_SIDE, PARTITION_GRID_SIDE)
                            local_system = [i for i in filter(lambda s: s.grid_pos == (x, y), self.star_map.locations)][0]
                            split = local_system.name.split(" ")
                            new_label = []
                            for part in split:
                                if part in prefix_system_names or part in secondary_system_names:
                                    new_label.append("{}.".format(part[0]))
                                else:
                                    new_label.append(part)
                            label_text = ""
                            index = 0
                            for part in new_label:
                                label_text += part
                                if index < len(new_label):
                                    label_text += " "
                                index += 1
                            font = pygame.font.Font(FONT_PATH, POLITICAL_MAP_FONT_SIZE) 
                            label = font.render(label_text, True, "green", "black")
                            if local_system.in_sensor_view or self.debug_mode:
                                color = faction_type_to_color(local_system.faction_type)
                                pygame.draw.rect(map_surface, color, rect)
                            else:
                                pygame.draw.rect(map_surface, COLOR_FOG, rect)
                            pygame.draw.rect(map_surface, "black", rect, 1)
                            label_x = x * PARTITION_GRID_SIDE + PARTITION_GRID_SIDE / 2 - label.get_width() / 2
                            label_y = y * PARTITION_GRID_SIDE + PARTITION_GRID_SIDE / 2 - label.get_height() / 2
                            map_surface.blit(label, (label_x, label_y))

                if not self.political_map_toggle:
                    # display star systems and garrisoned fleets:
                    font = pygame.font.Font(FONT_PATH, STAR_SYSTEM_FONT_SIZE)
                    for loc in self.star_map.locations:
                        if loc.locationType == LocationType.STAR_SYSTEM:
                            if loc.in_sensor_view:
                                if loc == self.selected_system or loc in self.multiple_locs_selected:
                                    pygame.draw.circle(map_surface, COLOR_SELECTION, loc.pos, SELECTION_RADIUS_PX, SELECTION_CIRCLE_WIDTH_PX)
                                pygame.draw.circle(map_surface, faction_type_to_color(loc.faction_type), loc.pos, STAR_RADIUS_PX, STAR_SYSTEM_LINE_WIDTH_PX)
                                text = None
                                if self.system_strength_overlay_mode:
                                    text = "{}".format(loc.ships)
                                elif self.sensor_range_overlay_mode:
                                    text = "{} LY".format(loc.sensor_range)
                                elif self.reenforcement_chance_overlay_mode:
                                    text = "{}%".format(loc.reenforce_chance_out_of_100)
                                text = font.render(text, True, "white")
                                pos = (loc.pos[0] - text.get_width() / 2, loc.pos[1] - text.get_height() / 2)
                                map_surface.blit(text, pos)
                            else:
                                pygame.draw.circle(map_surface, COLOR_FOGGED_STAR, loc.pos, STAR_RADIUS_PX)

                    def draw_fleet(fleet):
                        if fleet.in_sensor_view:
                            valid = True
                            if fleet in self.multiple_fleets_clicked:
                                if fleet is not self.selected_fleet:
                                    valid = False
                            line_color = COLOR_SENSOR
                            if fleet is self.selected_fleet:
                                line_color = "yellow"
                            pygame.draw.line(map_surface, line_color, fleet.pos, fleet.destination.pos)
                            if valid:
                                top = (fleet.pos[0], fleet.pos[1] - STAR_RADIUS_PX)
                                bottom = (fleet.pos[0], fleet.pos[1] + STAR_RADIUS_PX)
                                right = (fleet.pos[0] + STAR_RADIUS_PX, fleet.pos[1])
                                left = (fleet.pos[0] - STAR_RADIUS_PX, fleet.pos[1])
                                color_1 = faction_type_to_color(fleet.faction_type)
                                color_2 = "white"
                                pygame.draw.polygon(map_surface, color_1, (top, right, bottom, left), 1)
                                fleet_size_text = font.render("{}".format(fleet.ships), True, color_2)
                                pos = (
                                    fleet.pos[0] - fleet_size_text.get_width() / 2,
                                    fleet.pos[1] - fleet_size_text.get_height() / 2)
                                map_surface.blit(fleet_size_text, pos)

                    # display deployed fleets:
                    for fleet in self.star_map.deployed_fleets:
                        draw_fleet(fleet) 
                    if self.selected_fleet is not None:
                        draw_fleet(self.selected_fleet) 

                    # display fuel range and sensor range for selected system
                    if self.selected_system is not None:
                        fuel_radius = DEFAULT_FUEL_RANGE_LY * LY
                        sensor_radius = self.selected_system.sensor_range * LY
                        pygame.draw.circle(map_surface, COLOR_FUEL_RANGE, self.selected_system.pos, fuel_radius, 1)
                        pygame.draw.circle(map_surface, COLOR_SENSOR, self.selected_system.pos, sensor_radius, 1)
                    # display sensor range for selected fleet
                    if self.selected_fleet is not None:
                        sensor_radius = DEFAULT_FLEET_SENSOR_RANGE_LY * LY
                        pygame.draw.circle(map_surface, COLOR_SENSOR, self.selected_fleet.pos, sensor_radius, 1)

                # Draw waypoint overlay if enabled:
                if self.routing_mode:

                    def draw_waypoints(fleet, color):
                        # draw lines from point to point
                        current = Vector2(fleet.pos).move_towards(Vector2(fleet.destination.pos), STAR_RADIUS_PX)
                        index = 0
                        for waypoint in fleet.waypoints: 
                            end = Vector2(waypoint.pos).move_towards(Vector2(current), STAR_RADIUS_PX + 5)
                            pygame.draw.line(map_surface, color, current, end, FLEET_ETA_LINE_WIDTH)
                            # draw end nubs:  # TODO: Procedural arrows instead of circular end-nubs
                            pygame.draw.circle(map_surface, color, end, 4) 
                            index += 1
                            if index < len(fleet.waypoints):
                                next_up = fleet.waypoints[index]
                                current = end.move_towards(Vector2(next_up.pos), STAR_RADIUS_PX)
                   
                    player_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER and x is not self.selected_fleet, self.star_map.deployed_fleets)]
                    for fleet in player_fleets: 
                        draw_waypoints(fleet, "yellow")

                    # draw the selected ones last, in a different color:
                    if self.selected_fleet is not None:
                        if self.selected_fleet.faction_type == FactionType.PLAYER:
                            draw_waypoints(self.selected_fleet, "cyan")

                # Draw click-and-drag box
                if self.drag_start and self.drag_end:
                    rect = click_and_drag_rect(self.drag_start, self.drag_end)
                    pygame.draw.rect(map_surface, COLOR_SENSOR, rect, 1)

                pygame.draw.rect(map_surface, "blue", (0, 0, MAP_WIDTH_PX, MAP_HEIGHT_PX), 1)
                self.screen.blit(map_surface, (0, 0))

            def draw_hud():
                hud_surface = pygame.Surface((HUD_WIDTH_PX, HUD_HEIGHT_PX))
                font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
                # General HUD stuff:
                end_turn_surface = font.render("End Turn", True, "red")
                hud_surface.blit(end_turn_surface, (0, 0))
                turn_text = "Turn: {}".format(self.turn)
                turn_surface = font.render(turn_text, True, "green")
                hud_surface.blit(turn_surface, (HUD_WIDTH_PX / 2, 0))

                # Selected System:
                if self.selected_system is None:
                    selected_system_text = "System: None"
                    selected_system_owner_text = "Owner: None"
                    selected_system_local_fleets_text = "Local Fleets: None"
                else:
                    faction_name = self.star_map.faction_names[self.selected_system.faction_type]
                    selected_system_text = "System: {}".format(self.selected_system.name)
                    selected_system_owner_text = "Owner: {}".format(faction_name)
                    selected_system_local_fleets_text = "Local Fleets: {} ({}% vets / +{})".format(self.selected_system.ships, self.selected_system.get_percent_vets(), self.selected_system.get_veterancy_roll_bonus())

                # TODO: System bonuses and peculiarities/modifiers

                selected_system_text_surface = font.render(selected_system_text, True, "green")
                hud_surface.blit(selected_system_text_surface, (0, HUD_FONT_SIZE + 1))

                selected_system_owner_surface = font.render(selected_system_owner_text, True, "green")
                hud_surface.blit(selected_system_owner_surface, (0, (HUD_FONT_SIZE + 1) * 2))

                selected_system_local_fleets_surface = font.render(selected_system_local_fleets_text, True, "green")
                hud_surface.blit(selected_system_local_fleets_surface, (0, (HUD_FONT_SIZE + 1) * 3))

                if self.selected_system.faction_type == FactionType.PLAYER:
                    # Deploy button
                    if len(self.multiple_locs_selected) > 1:
                        num_ships = sum([i for i in map(lambda x: x.ships - 1, self.multiple_locs_selected)])
                        deploy_color = "red"
                        deploy_surface = font.render(
                            "({}) Deploy Multiple!".format(num_ships), True, deploy_color)
                        hud_surface.blit(deploy_surface, (60, (HUD_FONT_SIZE + 1) * 4))
                        if num_ships > 0:
                            rect = (59, (HUD_FONT_SIZE + 1) * 4 - 1, deploy_surface.get_width() + 2,
                                    deploy_surface.get_height() + 2)
                            pygame.draw.rect(hud_surface, "green", rect, 1)
                    else:
                        deploy_up_surface = font.render("[+]", True, "green")
                        hud_surface.blit(deploy_up_surface, (0, (HUD_FONT_SIZE + 1) * 4))
                        deploy_down_surface = font.render("[-]", True, "green")
                        hud_surface.blit(deploy_down_surface, (30, (HUD_FONT_SIZE + 1) * 4))
                        deploy_color = "red"
                        deploy_surface = font.render(
                            "{}/{} Deploy!".format(self.deploy_amount, self.selected_system.ships - 1), True, deploy_color)
                        hud_surface.blit(deploy_surface, (60, (HUD_FONT_SIZE + 1) * 4))
                        if self.deploy_amount > 0:
                            rect = (59, (HUD_FONT_SIZE + 1) * 4 - 1, deploy_surface.get_width() + 2,
                                    deploy_surface.get_height() + 2)
                            pygame.draw.rect(hud_surface, "green", rect, 1)

                # Reenforce button
                reenforce_up_surface = font.render("[+]", True, "green")
                hud_surface.blit(reenforce_up_surface, (0, (HUD_FONT_SIZE + 1) * 5))
                reenforce_down_surface = font.render("[-]", True, "green")
                hud_surface.blit(reenforce_down_surface, (30, (HUD_FONT_SIZE + 1) * 5))
                reenforce_color = "yellow"
                reenforce_surface = font.render(
                    "{}/{} Reenforce!".format(self.reenforce_amount, self.player_reenforcement_pool), True,
                    reenforce_color)
                hud_surface.blit(reenforce_surface, (60, (HUD_FONT_SIZE + 1) * 5))
                if self.reenforce_amount > 0:
                    rect = (59, (HUD_FONT_SIZE + 1) * 5 - 1, reenforce_surface.get_width() + 2,
                            reenforce_surface.get_height() + 2)
                    pygame.draw.rect(hud_surface, "green", rect, 1)

                # TODO: ^ A class for those two buttons.

                reenforce_chance_text = "Reenforce Chance: {}%".format(self.selected_system.reenforce_chance_out_of_100)
                reenforce_chance_surface = font.render(reenforce_chance_text, True, "green")
                hud_surface.blit(reenforce_chance_surface, (0, (HUD_FONT_SIZE + 1) * 6))

                sensor_range_text = "Sensor Range: {} LY".format(self.selected_system.sensor_range)
                sensor_range_surface = font.render(sensor_range_text, True, "green")
                hud_surface.blit(sensor_range_surface, (0, (HUD_FONT_SIZE + 1) * 7))

                fuel_range_text = "Fuel Range: {} LY".format(DEFAULT_FUEL_RANGE_LY)
                fuel_range_surface = font.render(fuel_range_text, True, "green")
                hud_surface.blit(fuel_range_surface, (0, (HUD_FONT_SIZE + 1) * 8))

                break_y = (HUD_FONT_SIZE + 1) * 9 + HUD_FONT_SIZE / 2
                pygame.draw.line(hud_surface, "red", (0, break_y), (HUD_WIDTH_PX, break_y), 1)

                # TODO: Refactor overlay buttons in to a class
                overlay_toggle_radius = HUD_FONT_SIZE / 3
                overlay_toggle_x = HUD_WIDTH_PX - overlay_toggle_radius - 10
                incoming_text = "Incoming Fleets Overlay"
                incoming_surface = font.render(incoming_text, True, "green")
                hud_surface.blit(incoming_surface, (0, (HUD_FONT_SIZE + 1) * 10))
                center = (overlay_toggle_x, (HUD_FONT_SIZE + 1) * 10 + incoming_surface.get_height() / 2)
                if self.incoming_fleets_overlay_mode:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius)
                else:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius, 1)

                outgoing_text = "Outgoing Fleets Overlay"
                outgoing_surface = font.render(outgoing_text, True, "green")
                hud_surface.blit(outgoing_surface, (0, (HUD_FONT_SIZE + 1) * 11))
                center = (overlay_toggle_x, (HUD_FONT_SIZE + 1) * 11 + outgoing_surface.get_height() / 2)
                if self.outgoing_fleets_overlay_mode:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius)
                else:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius, 1)

                strength_text = "System Strength Overlay"
                strength_surface = font.render(strength_text, True, "green")
                hud_surface.blit(strength_surface, (0, (HUD_FONT_SIZE + 1) * 12))
                center = (overlay_toggle_x, (HUD_FONT_SIZE + 1) * 12 + strength_surface.get_height() / 2)
                if self.system_strength_overlay_mode:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius)
                else:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius, 1)

                reenforce_text = "Reenforcement Overlay"
                reenforce_surface = font.render(reenforce_text, True, "green")
                hud_surface.blit(reenforce_surface, (0, (HUD_FONT_SIZE + 1) * 13))
                center = (overlay_toggle_x, (HUD_FONT_SIZE + 1) * 13 + reenforce_surface.get_height() / 2)
                if self.reenforcement_chance_overlay_mode:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius)
                else:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius, 1)

                sensor_text = "Sensor Range Overlay"
                sensor_surface = font.render(sensor_text, True, "green")
                hud_surface.blit(sensor_surface, (0, (HUD_FONT_SIZE + 1) * 14))
                center = (overlay_toggle_x, (HUD_FONT_SIZE + 1) * 14 + reenforce_surface.get_height() / 2)
                if self.sensor_range_overlay_mode:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius)
                else:
                    pygame.draw.circle(hud_surface, "green", center, overlay_toggle_radius, 1)

                break_y = (HUD_FONT_SIZE + 1) * 15 + HUD_FONT_SIZE / 2
                pygame.draw.line(hud_surface, "red", (0, break_y), (HUD_WIDTH_PX, break_y), 1)

                # Selected Fleet:
                if self.selected_fleet is None:
                    selected_fleet_text = "Fleet: None"
                    selected_fleet_owner_text = "Owner: None"
                    selected_fleet_size_text = "Fleet Size: None"
                    selected_fleet_destination_text = "Destination: None"
                    selected_fleet_eta_text = "ETA: None"
                else:
                    faction_name = self.star_map.faction_names[self.selected_fleet.faction_type]
                    selected_fleet_text = "Fleet: {}".format(self.selected_fleet.name)
                    selected_fleet_owner_text = "Owner: {}".format(faction_name)
                    selected_fleet_size_text = "Fleet Size: {} ({}% vets / +{})".format(self.selected_fleet.ships, self.selected_fleet.get_percent_vets(), self.selected_fleet.get_veterancy_roll_bonus())
                    selected_fleet_destination_text = "Destination: {}".format(self.selected_fleet.destination.name)
                    selected_fleet_eta_text = "ETA: {} turns".format(self.selected_fleet.get_eta())

                selected_fleet_text_surface = font.render(selected_fleet_text, True, "green")
                hud_surface.blit(selected_fleet_text_surface, (0, (HUD_FONT_SIZE + 1) * 16))

                selected_fleet_owner_surface = font.render(selected_fleet_owner_text, True, "green")
                hud_surface.blit(selected_fleet_owner_surface, (0, (HUD_FONT_SIZE + 1) * 17))

                selected_fleet_size_surface = font.render(selected_fleet_size_text, True, "green")
                hud_surface.blit(selected_fleet_size_surface, (0, (HUD_FONT_SIZE + 1) * 18))

                selected_fleet_destination_surface = font.render(selected_fleet_destination_text, True, "green")
                hud_surface.blit(selected_fleet_destination_surface, (0, (HUD_FONT_SIZE + 1) * 19))

                selected_fleet_eta_surface = font.render(selected_fleet_eta_text, True, "green")
                hud_surface.blit(selected_fleet_eta_surface, (0, (HUD_FONT_SIZE + 1) * 20))

                break_y = (HUD_FONT_SIZE + 1) * 21 + HUD_FONT_SIZE / 2
                pygame.draw.line(hud_surface, "red", (0, break_y), (HUD_WIDTH_PX, break_y), 1)

                # Victory condition information: 
                vic_text = font.render("Victory Progress:", True, "green")
                hud_surface.blit(vic_text, (0, (HUD_FONT_SIZE + 1) * 22))

                if not self.exogalactic_invasion_begun:
                    vic_empires = font.render("{}/{} Empires Remaining".format(self.remaining_factions, NUM_AI_EMPIRES), True, "green")
                    hud_surface.blit(vic_empires, (0, (HUD_FONT_SIZE + 1) * 24))
                    rect = (HUD_WIDTH_PX - HUD_CHECKBOX_WIDTH - 10, (HUD_FONT_SIZE + 1) * 24, HUD_CHECKBOX_WIDTH, HUD_FONT_SIZE)
                    pygame.draw.rect(hud_surface, "green", rect, 1)
                    if self.all_ai_empires_destroyed: # TODO: A separate function for ze checkmarks
                        one = (rect[0] - 4, rect[1] + 4)
                        two = (rect[0] + HUD_CHECKBOX_WIDTH / 2, rect[1] + HUD_FONT_SIZE - 4)
                        three = (rect[0] + HUD_CHECKBOX_WIDTH - 5, rect[1] - 10)
                        pygame.draw.line(hud_surface, "green", one, two, 2)
                        pygame.draw.line(hud_surface, "green", two, three, 2)

                    vic_pirates = font.render("All Pirates Defeated", True, "green")
                    hud_surface.blit(vic_pirates, (0, (HUD_FONT_SIZE + 1) * 26))
                    rect = (HUD_WIDTH_PX - HUD_CHECKBOX_WIDTH - 10, (HUD_FONT_SIZE + 1) * 26, HUD_CHECKBOX_WIDTH, HUD_FONT_SIZE)
                    pygame.draw.rect(hud_surface, "green", rect, 1)
                    if self.all_pirates_destroyed:
                        one = (rect[0] - 4, rect[1] + 4)
                        two = (rect[0] + HUD_CHECKBOX_WIDTH / 2, rect[1] + HUD_FONT_SIZE - 4)
                        three = (rect[0] + HUD_CHECKBOX_WIDTH - 5, rect[1] - 10)
                        pygame.draw.line(hud_surface, "green", one, two, 2)
                        pygame.draw.line(hud_surface, "green", two, three, 2)

                    vic_percent = font.render("Sector {}/{}% Conquered".format(round(self.conquest_percent), CONQUEST_PERCENT_FOR_VICTORY), True, "green")
                    hud_surface.blit(vic_percent, (0, (HUD_FONT_SIZE + 1) * 28))
                    rect = (HUD_WIDTH_PX - HUD_CHECKBOX_WIDTH - 10, (HUD_FONT_SIZE + 1) * 28, HUD_CHECKBOX_WIDTH, HUD_FONT_SIZE)
                    pygame.draw.rect(hud_surface, "green", rect, 1)
                    if self.conquest_percent >= CONQUEST_PERCENT_FOR_VICTORY:
                        one = (rect[0] - 4, rect[1] + 4)
                        two = (rect[0] + HUD_CHECKBOX_WIDTH / 2, rect[1] + HUD_FONT_SIZE - 4)
                        three = (rect[0] + HUD_CHECKBOX_WIDTH - 5, rect[1] - 10)
                        pygame.draw.line(hud_surface, "green", one, two, 2)
                        pygame.draw.line(hud_surface, "green", two, three, 2)

                else:
                    vic_invaders = font.render("Throw Back the Invaders!", True, "green")
                    hud_surface.blit(vic_invaders, (0, (HUD_FONT_SIZE + 1) * 24))
                    vic_waves = font.render("Waves Survived: {}".format(self.invasion_waves_completed), True, "green")
                    hud_surface.blit(vic_waves, (0, (HUD_FONT_SIZE + 1) * 25))
                    if self.invasion_fleets_spawned:
                        if self.invasion_waves_completed < EXOGALACTIC_INVASION_WAVE_LIMIT:
                            next_wave_min = self.turn_of_last_wave + EXOGALACTIC_WAVE_DELAY_MIN
                            next_wave_max = self.turn_of_last_wave + EXOGALACTIC_WAVE_DELAY_MAX
                            vic_next_wave = font.render("Next: turn {} - {}".format(next_wave_min, next_wave_max), True, "green")
                            hud_surface.blit(vic_next_wave, (0, (HUD_FONT_SIZE + 1) * 26))
                        else:
                            vic_next_wave = font.render("All Waves Completed", True, "green")
                            hud_surface.blit(vic_next_wave, (0, (HUD_FONT_SIZE + 1) * 26))

                pygame.draw.rect(hud_surface, "red", (0, 0, HUD_WIDTH_PX, HUD_HEIGHT_PX), 1)
                self.screen.blit(hud_surface, (MAP_WIDTH_PX, 0))

            def draw_console(): 
                console_surface = pygame.Surface((CONSOLE_WIDTH_PX, CONSOLE_HEIGHT_PX))
                pygame.draw.rect(console_surface, "green", (0, 0, CONSOLE_WIDTH_PX, CONSOLE_HEIGHT_PX), 1)
                font = pygame.font.Font(FONT_PATH, CONSOLE_FONT_SIZE)
                line_height = CONSOLE_FONT_SIZE + CONSOLE_FONT_PADDING_PX
                lines = CONSOLE_HEIGHT_PX // line_height
                last = len(self.console.messages) - 1 
                msgs = []
                self.console_clickables = []
                for line in range(lines):
                    index = last - line - self.console_scrolled_up_by
                    if index >= 0 and index < len(self.console.messages):
                        msgs.append(self.console.messages[index])

                msgs.reverse() 
                for line in range(len(msgs)):
                    line_surface = font.render(msgs[line]["msg"], True, "green")
                    console_surface.blit(line_surface, (0, line * line_height))
                    attachment = msgs[line]["attachment"]
                    if attachment is not None:
                        rect = (0, MAP_HEIGHT_PX + line * line_height, CONSOLE_WIDTH_PX, line_height)
                        self.console_clickables.append(Clickable(rect, attachment)) 

                self.screen.blit(console_surface, (0, MAP_HEIGHT_PX))

            def draw_battle_graph():
                graph = self.displaying_battle_graph
                y_atk = graph.starting_ships["attacker"]
                y_def = graph.starting_ships["defender"]
                max_x = len(graph.ships_by_side_per_round)
                max_y = max(y_atk, y_def)
                graph_surface = pygame.Surface((max_x, max_y))
                atk_color = graph.colors["attacker"]
                def_color = graph.colors["defender"]
                for x in range(1, max_x):
                    pygame.draw.line(graph_surface, atk_color, (x - 1, y_atk), (x, graph.ships_by_side_per_round[x]["attacker"]), 1)
                    y_atk = graph.ships_by_side_per_round[x]["attacker"]
                    pygame.draw.line(graph_surface, def_color, (x - 1, y_def), (x, graph.ships_by_side_per_round[x]["defender"]), 1)
                    y_def = graph.ships_by_side_per_round[x]["defender"]

                graph_surface = pygame.transform.scale(graph_surface, (SCREEN_WIDTH_PX, GRAPH_HEIGHT_PX))
                graph_surface = pygame.transform.flip(graph_surface, False, True)
                self.screen.fill((30, 30, 30))
                self.screen.blit(graph_surface, (0, 0))
                font = pygame.font.Font(FONT_PATH, CONSOLE_FONT_SIZE) 
                battle_text = font.render("{} (turn {}) (player in green)".format(graph.battle_name, graph.battle_turn), True, "white")
                self.screen.blit(battle_text, (0, GRAPH_HEIGHT_PX))
                atk_text = font.render("attacker started with {} ships and ended with {}".format(graph.starting_ships["attacker"], y_atk), True, atk_color)
                self.screen.blit(atk_text, (0, GRAPH_HEIGHT_PX + CONSOLE_FONT_SIZE + 1))
                def_text = font.render("defender started with {} ships and ended with {}".format(graph.starting_ships["defender"], y_def), True, def_color)
                self.screen.blit(def_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 2))
                xp_text = font.render("attacker had +{} XP bonuses while defender had +{}".format(graph.xp_bonuses["attacker"], graph.xp_bonuses["defender"]), True, "white")
                self.screen.blit(xp_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 3))
                charge_text = font.render("attacker 'charge!': {}".format(graph.charge), True, "white")
                self.screen.blit(charge_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 4))
                ls_text = font.render("defender 'last stand!': {}".format(graph.last_stand), True, "white")
                self.screen.blit(ls_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 5))

            def draw_stats_graph():
                max_x = len(self.systems_over_time)
                max_y = max(max(self.systems_over_time), max(self.deployed_fleets_over_time), max(self.decimated_systems_over_time))
                graph_surface = pygame.Surface((max_x, max_y))
                y_systems = self.systems_over_time[0]
                y_fleets = self.deployed_fleets_over_time[0]
                y_decimated = self.decimated_systems_over_time[0]
                for x in range(1, max_x):
                    if x == self.coalition_stage_turn or x == self.invader_stage_turn:
                        pygame.draw.line(graph_surface, "white", (x, 0), (x, max_y), 1)
                    pygame.draw.line(graph_surface, "cyan", (x - 1, y_systems), (x, self.systems_over_time[x]), 1)
                    y_systems = self.systems_over_time[x]
                    pygame.draw.line(graph_surface, "magenta", (x - 1, y_fleets), (x, self.deployed_fleets_over_time[x]), 1)
                    y_fleets = self.deployed_fleets_over_time[x]
                    pygame.draw.line(graph_surface, "red", (x - 1, y_decimated), (x, self.decimated_systems_over_time[x]), 1)
                    y_decimated = self.decimated_systems_over_time[x]
                graph_surface = pygame.transform.scale(graph_surface, (SCREEN_WIDTH_PX, GRAPH_HEIGHT_PX))
                graph_surface = pygame.transform.flip(graph_surface, False, True)
                self.screen.fill((30, 30, 30))
                self.screen.blit(graph_surface, (0, 0))
                font = pygame.font.Font(FONT_PATH, CONSOLE_FONT_SIZE) 
                turn_text = font.render("turn {}".format(self.turn), True, "white")
                self.screen.blit(turn_text, (0, GRAPH_HEIGHT_PX))
                systems_text = font.render("player has {} systems".format(y_systems), True, "cyan")
                self.screen.blit(systems_text, (0, GRAPH_HEIGHT_PX + CONSOLE_FONT_SIZE + 1))
                fleets_text = font.render("player has {} deployed fleets".format(y_fleets), True, "magenta")
                self.screen.blit(fleets_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 2))
                decimated_text = font.render("{} systems decimated".format(y_decimated), True, "red")
                self.screen.blit(decimated_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 3))

            def draw_fleets_graph():
                max_x = len(self.ships_over_time)
                max_y = max(max(self.enemy_ships_over_time), max(self.veteran_ships_over_time), max(self.ships_over_time))
                graph_surface = pygame.Surface((max_x, max_y))
                y_ships = self.ships_over_time[0]
                y_vets = self.veteran_ships_over_time[0]
                y_enemies = self.enemy_ships_over_time[0]
                for x in range(1, max_x):
                    if x == self.coalition_stage_turn or x == self.invader_stage_turn:
                        pygame.draw.line(graph_surface, "white", (x, 0), (x, max_y), 1)
                    pygame.draw.line(graph_surface, "green", (x - 1, y_ships), (x, self.ships_over_time[x]), 1)
                    y_ships = self.ships_over_time[x]
                    pygame.draw.line(graph_surface, "yellow", (x - 1, y_vets), (x, self.veteran_ships_over_time[x]), 1)
                    y_vets = self.veteran_ships_over_time[x]
                    pygame.draw.line(graph_surface, "red", (x - 1, y_enemies), (x, self.enemy_ships_over_time[x]), 1)
                    y_enemies = self.enemy_ships_over_time[x]
                graph_surface = pygame.transform.scale(graph_surface, (SCREEN_WIDTH_PX, GRAPH_HEIGHT_PX))
                graph_surface = pygame.transform.flip(graph_surface, False, True)
                self.screen.fill((30, 30, 30))
                self.screen.blit(graph_surface, (0, 0))
                font = pygame.font.Font(FONT_PATH, CONSOLE_FONT_SIZE) 
                turn_text = font.render("turn {}".format(self.turn), True, "white")
                self.screen.blit(turn_text, (0, GRAPH_HEIGHT_PX))
                ships_text = font.render("player has {} ships ".format(y_ships), True, "green")
                self.screen.blit(ships_text, (0, GRAPH_HEIGHT_PX + CONSOLE_FONT_SIZE + 1))
                vets_text = font.render("player has {} veteran ships ".format(y_vets), True, "yellow")
                self.screen.blit(vets_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 2))
                enemies_text = font.render("opponents have {} ships ".format(y_enemies), True, "red")
                self.screen.blit(enemies_text, (0, GRAPH_HEIGHT_PX + (CONSOLE_FONT_SIZE + 1) * 3))

            # clear display
            self.screen.fill("white")

            if no_graphs_being_presented():
                # draw game to screen surface:
                draw_map()
                draw_hud()
                draw_console()

                # End-game splashes
                if self.game_over_mode:
                    game_over_splash()
                elif self.victory_mode:
                    victory_splash()

                # Draw deploy mode ETA hover lines
                if self.deploy_mode and self.eta_line_mode: 
                    if len(self.multiple_locs_selected) > 0:
                        for loc in self.multiple_locs_selected:
                            if loc.ly_to(self.eta_line_target.pos) <= DEFAULT_FUEL_RANGE_LY:
                                draw_eta_line(loc, self.eta_line_target) 
                    else:
                        draw_eta_line(self.selected_system, self.eta_line_target) 

                if self.incoming_fleets_overlay_mode:
                    draw_incoming_fleets_overlay()  

                if self.outgoing_fleets_overlay_mode:
                    draw_outgoing_fleets_overlay()  

            elif self.displaying_battle_graph:
                draw_battle_graph()
            elif self.displaying_fleets_graph:
                draw_fleets_graph()
            elif self.displaying_stats_graph:
                draw_stats_graph()

            self.display_changed = False
            pygame.display.flip()

        def stats_check():
            player_systems = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.locations)]
            player_fleets = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.deployed_fleets)]
            player_ships = sum(map(lambda x: x.ships, player_systems))
            player_ships += sum(map(lambda x: x.ships, player_fleets))
            vet_ships = sum(map(lambda y: y.get_num_vets(), filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.locations)))
            vet_ships += sum(map(lambda y: y.get_num_vets(), filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.deployed_fleets)))
            enemy_systems = [i for i in filter(lambda x: x.faction_type != FactionType.PLAYER, self.star_map.locations)]
            enemy_fleets = [i for i in filter(lambda x: x.faction_type != FactionType.PLAYER, self.star_map.deployed_fleets)]
            player_ships = sum(map(lambda x: x.ships, player_systems))
            player_ships += sum(map(lambda x: x.ships, player_fleets))
            enemy_ships = sum(map(lambda x: x.ships, enemy_systems))
            enemy_ships += sum(map(lambda x: x.ships, enemy_fleets))
            self.ships_over_time.append(player_ships)
            self.systems_over_time.append(len(player_systems))
            self.veteran_ships_over_time.append(vet_ships)
            self.enemy_ships_over_time.append(enemy_ships)
            self.deployed_fleets_over_time.append(len(player_fleets))
            decimated_systems = [i for i in filter(lambda x: x.decimated, self.star_map.locations)]
            self.decimated_systems_over_time.append(len(decimated_systems))

        def eta_line_check(pos): 
            found = False           
            for loc in self.can_deploy_to:  
                if loc.clicked(pos):   
                    self.eta_line_mode = True 
                    self.eta_line_target = loc  
                    self.display_changed = True 
                    found = True
                    break
            if not found and self.eta_line_mode:
                self.eta_line_mode = False
                self.display_changed = True 

        def check_incoming_fleets_overlay_clicks(pos):
            if self.incoming_fleets_overlay_button.clicked(pos):
                self.incoming_fleets_overlay_mode = not self.incoming_fleets_overlay_mode
                self.display_changed = True

        def check_outgoing_fleets_overlay_clicks(pos):
            if self.outgoing_fleets_overlay_button.clicked(pos):
                self.outgoing_fleets_overlay_mode = not self.outgoing_fleets_overlay_mode
                self.display_changed = True

        # NOTE: While the above two buttons can be toggled on/off at will,
        #       the next three buttons are mutually exclusive toggles.

        def check_system_strength_overlay_clicks(pos):
            if self.system_strength_overlay_button.clicked(pos):
                self.system_strength_overlay_mode = True
                self.sensor_range_overlay_mode = False
                self.reenforcement_chance_overlay_mode = False
                self.display_changed = True

        def check_sensor_range_overlay_clicks(pos):
            if self.sensor_range_overlay_button.clicked(pos):
                self.system_strength_overlay_mode = False
                self.sensor_range_overlay_mode = True
                self.reenforcement_chance_overlay_mode = False
                self.display_changed = True

        def check_reenforcement_chance_overlay_clicks(pos):
            if self.reenforcement_chance_overlay_button.clicked(pos):
                self.system_strength_overlay_mode = False
                self.sensor_range_overlay_mode = False
                self.reenforcement_chance_overlay_mode = True
                self.display_changed = True

        def off_map_pirate_raid_check():
            if self.exogalactic_invasion_begun:
                return
            if d100()[0] <= OFF_MAP_RAID_CHANCE_OUT_OF_100:  
                targets = []
                for system in self.star_map.locations:
                    in_range_x = system.pos[0] < DEFAULT_FUEL_RANGE_LY or system.pos[0] > MAP_WIDTH_PX - DEFAULT_FUEL_RANGE_LY
                    in_range_y = system.pos[1] < DEFAULT_FUEL_RANGE_LY or system.pos[1] > MAP_HEIGHT_PX - DEFAULT_FUEL_RANGE_LY
                    if in_range_x or in_range_y:
                        targets.append(system)
                target = choice(targets)
                pos = target.pos
                if target.pos[0] < DEFAULT_FUEL_RANGE_LY:
                    pos = (target.pos[0] - DEFAULT_FUEL_RANGE_LY, target.pos[1])
                elif target.pos[0] > MAP_WIDTH_PX - DEFAULT_FUEL_RANGE_LY:
                    pos = (target.pos[0] + DEFAULT_FUEL_RANGE_LY, target.pos[1])
                elif target.pos[1] < DEFAULT_FUEL_RANGE_LY:
                    pos = (target.pos[0], target.pos[1] - DEFAULT_FUEL_RANGE_LY)
                else:
                    pos = (target.pos[0], target.pos[1] + DEFAULT_FUEL_RANGE_LY)
                num_ships = randint(int(target.ships * .9), int(target.ships * 1.1))
                if num_ships < 1:
                    num_ships = 1
                fleet = Fleet(self.star_map.name_a_fleet(FactionType.PIRATES), pos, FactionType.PIRATES, num_ships, target, randint(0, 100)) 
                self.star_map.deployed_fleets.append(fleet)

        def watch_mode_check():
            if self.watch_mode:
                self.watch_timer += 1
                if self.watch_timer == WATCH_TIMER_RATE:
                    self.watch_timer = 0
                    self.turn_processing_mode = True

        def no_graphs_being_presented():
            no_battle_graph = self.displaying_battle_graph is None
            no_stats_graph = self.displaying_stats_graph == False
            no_fleets_graph = self.displaying_fleets_graph == False
            return no_battle_graph and no_stats_graph and no_fleets_graph

        def strategic_mode():
            # handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    # quit game:
                    self.running = False
                if event.type == MOUSEBUTTONDOWN and not self.turn_processing_mode and no_graphs_being_presented():
                    if not self.drag_start:
                        self.drag_start = pygame.mouse.get_pos()
                elif event.type == MOUSEBUTTONUP and not self.turn_processing_mode and no_graphs_being_presented():
                    # drag-selected locations
                    if self.drag_start and self.drag_end:
                        self.multiple_locs_selected = []
                        selection_rect = pygame.Rect(click_and_drag_rect(self.drag_start, self.drag_end))
                        for loc in self.star_map.locations:
                            if loc.faction_type == FactionType.PLAYER and selection_rect.contains(((loc.pos), (0, 0))):
                                self.multiple_locs_selected.append(loc)
                        if len(self.multiple_locs_selected) > 0:
                            self.selected_system = self.multiple_locs_selected[0]
                    self.drag_start = None
                    self.drag_end = None
                    self.display_changed = True
                    # TODO: Maybe something for drag-selected fleets, too
                    # Mouse clicks
                    shift = pygame.key.get_pressed()[K_LSHIFT] or pygame.key.get_pressed()[K_RSHIFT]
                    ctrl = pygame.key.get_pressed()[K_LCTRL] or pygame.key.get_pressed()[K_RCTRL]
                    pos = pygame.mouse.get_pos()
                    check_location_clicks(pos)
                    check_console_clickables(pos) 
                    check_deploy_button_clicks(pos, shift, ctrl)
                    check_reenforce_button_clicks(pos, shift, ctrl)
                    check_fleet_clicks(pos)
                    check_end_turn_clicks(pos)
                    check_incoming_fleets_overlay_clicks(pos)
                    check_outgoing_fleets_overlay_clicks(pos)
                    check_system_strength_overlay_clicks(pos)
                    check_reenforcement_chance_overlay_clicks(pos)
                    check_sensor_range_overlay_clicks(pos)
                elif event.type == KEYDOWN and not self.turn_processing_mode:
                    # Buttons
                    shift = pygame.key.get_pressed()[K_LSHIFT] or pygame.key.get_pressed()[K_RSHIFT]
                    ctrl = pygame.key.get_pressed()[K_LCTRL] or pygame.key.get_pressed()[K_RCTRL]
                    if pygame.key.get_pressed()[K_SPACE] and no_graphs_being_presented():
                        self.turn_processing_mode = True
                    elif pygame.key.get_pressed()[K_ESCAPE]:
                        if self.deploy_mode:
                            self.deploy_mode = False
                            self.console.push("Deploy mode cancelled")
                            self.display_changed = True
                        if self.reenforce_mode:
                            self.reenforce_mode = False
                            self.console.push("Reenforce mode cancelled")
                            self.display_changed = True
                        if self.displaying_battle_graph is not None:
                            self.displaying_battle_graph = None
                            self.display_changed = True
                        if self.displaying_stats_graph:
                            self.displaying_stats_graph = False
                            self.display_changed = True
                        if self.displaying_fleets_graph:
                            self.displaying_fleets_graph = False
                            self.display_changed = True
                        if self.political_map_toggle:
                            self.political_map_toggle = False
                            self.display_changed = True
                    elif pygame.key.get_pressed()[K_b] and shift and ctrl and no_graphs_being_presented():
                        self.skipping_tactical_battles = not self.skipping_tactical_battles
                        self.console.push("Skipping Tactical Battles: {}".format(self.skipping_tactical_battles))
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_r] and shift and ctrl and no_graphs_being_presented():
                        self.routing_mode = not self.routing_mode
                        self.console.push("Routing Mode: {}".format(self.routing_mode))
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_w] and shift and ctrl and no_graphs_being_presented():
                        self.watch_mode = not self.watch_mode
                        self.console.push("Watch Mode: {}".format(self.watch_mode))
                        self.display_changed = True
                        if self.watch_mode and FactionType.PLAYER not in self.ai_factions:
                            self.ai_factions.append(Faction(FactionType.PLAYER, self, Water()))
                        elif not self.watch_mode and FactionType.PLAYER in self.ai_factions:
                            self.ai_factions.remove(FactionType.PLAYER)
                            self.watch_timer = 0
                    elif pygame.key.get_pressed()[K_d] and shift and ctrl and no_graphs_being_presented():
                        self.debug_mode = not self.debug_mode
                        self.console.push("Debug Mode: {}".format(self.debug_mode))
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_s] and ctrl and shift and no_graphs_being_presented():
                        self.displaying_stats_graph = True
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_f] and ctrl and shift and no_graphs_being_presented():
                        self.displaying_fleets_graph = True
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_TAB] and no_graphs_being_presented():
                        if len(self.multiple_fleets_clicked) > 1:
                            self.clicked_fleets_index = (self.clicked_fleets_index + 1) % len(self.multiple_fleets_clicked)
                            self.selected_fleet = self.multiple_fleets_clicked[self.clicked_fleets_index]
                            self.display_changed = True
                    elif pygame.key.get_pressed()[K_d] and no_graphs_being_presented():
                        activate_deploy_mode()
                    elif pygame.key.get_pressed()[K_j] and no_graphs_being_presented():
                        if self.console_scrolled_up_by > 0:
                            self.console_scrolled_up_by -= 1
                            self.display_changed = True
                    elif pygame.key.get_pressed()[K_k] and no_graphs_being_presented():
                        if len(self.console.messages) - (self.console_scrolled_up_by + 1) >= len(INTRO_STRINGS):
                            self.console_scrolled_up_by += 1
                            self.display_changed = True
                    elif pygame.key.get_pressed()[K_p] and no_graphs_being_presented():
                        self.political_map_toggle = not self.political_map_toggle
                        self.console.push("Political Map View: {}".format(self.political_map_toggle))
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_h] and shift and ctrl and no_graphs_being_presented():
                        self.hard_mode = not self.hard_mode
                        self.console.push("Hard Mode: {}".format(self.hard_mode))
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_c] and shift and ctrl and no_graphs_being_presented():
                        self.close_battles_toggle = not self.close_battles_toggle
                        self.console.push("Watching Close Battles Only: {}".format(self.close_battles_toggle))
                        self.display_changed = True
                elif event.type == MOUSEMOTION and not self.turn_processing_mode and no_graphs_being_presented():
                    rel = pygame.mouse.get_rel()
                    if rel != (0, 0): # Avoid "very small" mouse movement detection distances
                        pos = pygame.mouse.get_pos()
                        # Click-and-drag box
                        if self.drag_start:
                            self.drag_end = pos
                            self.display_changed = True
                        # ETA Line Hover Checks
                        if self.deploy_mode:
                            eta_line_check(pos)
                            self.mouse_last = pos  
            
            # Handle processing between turns
            game_on = not (self.game_over_mode or self.victory_mode)
            if self.turn_processing_mode and game_on: 
                draw_processing_blurb()
                off_map_pirate_raid_check() 
                update_fleets()
                resolve_fleet_arrivals()
                remove_fleets()
                last_faction_buff_check()
                spawn_reenforcements()
                run_ai_behavior()
                stats_check() 
                game_over_check()
                victory_check()
                exogalactic_invader_countdown_check()
                self.turn += 1
                self.deploy_amount = 0
                self.reenforce_amount = 0
                self.multiple_fleets_clicked = []
                self.clicked_fleets_index = 0
                self.console_scrolled_up_by = 0
                self.turn_processing_mode = False
                self.display_changed = True
            elif game_on:
                watch_mode_check()

            # Draw main display if it has changed
            if self.display_changed:
                draw_display()   

        def tactical_mode(): 
            battle = self.tactical_battles[0]
            attacker_faction_name = self.star_map.faction_names[battle.attacker_faction]
            defender_faction_name = self.star_map.faction_names[battle.defender_faction]
            font = pygame.font.Font(FONT_PATH, TACTICAL_MODE_FONT_SIZE)
            battle.update_prompt_text(attacker_faction_name, defender_faction_name)
            end_font = pygame.font.Font(FONT_PATH, TACTICAL_BATTLE_RESULT_FONT_SIZE)
            result_color = "green"
            if battle.winner != FactionType.PLAYER:
                result_color = "red"
            if battle.attacker_faction == battle.winner:
                victory_text = end_font.render("{} lost {} defending {}".format(defender_faction_name, battle.fleet.name, battle.location.name), True, result_color, "black")
            elif battle.retreat:
                victory_text = end_font.render("{} from {} retreats in defeat from {}.".format(battle.fleet.name, attacker_faction_name, battle.location.name), True, result_color, "black")
            else:
                victory_text = end_font.render("{} from {} destroyed assaulting {}".format(battle.fleet.name, attacker_faction_name, battle.location.name), True, result_color, "black")

            def draw_tactical_mode():
                self.screen.blit(battle.starfield, (0, 0))
                self.screen.blit(battle.prompt_text, (7, 7))
                if battle.roll_text is not None:
                    self.screen.blit(battle.roll_text, (7, 30))
                for sprite in battle.attacker_sprites:
                    sprite.draw(self.screen) 
                    sprite.fire_laser(self.screen)  
                    sprite.move()  
                for sprite in battle.defender_sprites:
                    sprite.draw(self.screen)
                    sprite.fire_laser(self.screen)  
                    sprite.move()  
                battle.missile_check(self.screen) 
                if self.tactical_battle_cooldown < TACTICAL_BATTLE_COOLDOWN:
                    x = SCREEN_WIDTH_PX / 2 - victory_text.get_width() / 2
                    y = SCREEN_HEIGHT_PX - victory_text.get_height() * 2
                    pos = (x, y)
                    self.screen.blit(victory_text, pos)
                pygame.display.flip()  

            def update_tactical_round():
                if battle.round < len(battle.rounds):
                    battle.damage_due_attackers += battle.rounds[battle.round]["attacker_losses"]
                    battle.damage_due_defenders += battle.rounds[battle.round]["defender_losses"]
                    battle.remaining_attacker_ships -= battle.rounds[battle.round]["attacker_losses"]
                    battle.remaining_defender_ships -= battle.rounds[battle.round]["defender_losses"]
                    battle.update_prompt_text(attacker_faction_name, defender_faction_name) 
                    battle.update_roll_text(attacker_faction_name, defender_faction_name) 
                    attacker_targets = [i for i in filter(lambda x: x.hit and not x.explosion, battle.attacker_sprites)]
                    while battle.damage_due_attackers > 0:
                        valid = [i for i in filter(lambda x: x.value <= battle.damage_due_attackers and not x.explosion, attacker_targets)]
                        if len(valid) == 0:
                            break
                        target = choice(valid)
                        target.explosion = True
                        battle.damage_due_attackers -= target.value
                    defender_targets = [i for i in filter(lambda x: x.hit and not x.explosion, battle.defender_sprites)]
                    while battle.damage_due_defenders > 0:
                        valid = [i for i in filter(lambda x: x.value <= battle.damage_due_defenders and not x.explosion,
                                                   defender_targets)]
                        if len(valid) == 0:
                            break
                        target = choice(valid)
                        target.explosion = True
                        battle.damage_due_defenders -= target.value
                else:
                    self.tactical_battle_cooldown -= 1
                    if self.tactical_battle_cooldown <= 0:
                        self.tactical_battle_over = True
                if battle.round == len(battle.rounds) and not battle.retreat:
                    if battle.winner == battle.attacker_faction:
                        sprites = battle.defender_sprites
                    else:
                        sprites = battle.attacker_sprites
                    for sprite in sprites:
                        sprite.explosion = True

                battle.round += 1

            # handle events
            for event in pygame.event.get():
                # quit game:
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN and pygame.key.get_pressed()[K_SPACE]:
                    self.tactical_battle_over = True

            if self.skipping_tactical_battles:
                self.tactical_battle_over = True

            if not self.tactical_battle_over:
                draw_tactical_mode() 
            if self.tactical_battle_ticker == TACTICAL_BATTLE_RATE:
                update_tactical_round()
                self.tactical_battle_ticker = 0
            else:
                self.tactical_battle_ticker += 1

            if self.tactical_battle_over:
                self.tactical_battles.pop(0)
                self.tactical_round = 1
                self.tactical_battle_cooldown = TACTICAL_BATTLE_COOLDOWN
                self.tactical_battle_over = False
                self.display_changed = True

        # Game loop
        stats_check()
        self.display_changed = True
        draw_display()
        while self.running:
            if len(self.tactical_battles) == 0: 
                strategic_mode() 
            elif len(self.tactical_battles) > 0: 
                tactical_mode()
            pygame.event.pump() 
            self.clock.tick(FPS)

def loading_screen():
    screen = pygame.display.get_surface()
    bg = generate_starfield()[0]
    font = pygame.font.Font(FONT_PATH, LOADING_SCREEN_FONT_SIZE)
    loading_text = font.render("...loading SECTOR 34...", True, COLOR_EXPLOSION, "black")
    screen.blit(bg, (0, 0))
    screen.blit(loading_text, ((SCREEN_WIDTH_PX // 2 - loading_text.get_width() // 2), (SCREEN_HEIGHT_PX // 2 - loading_text.get_height() // 2)))
    pygame.display.flip()

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Sector 34     <version {}>".format(VERSION))
    icon = pygame.image.load(WINDOW_ICON_PATH)
    pygame.display.set_icon(icon)
    pygame.display.set_mode((SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX))
    # I'll include music and SFX down the road, perhaps
    # NOTE: procedural music! That's a good idea
    pygame.mixer.quit()
    loading_screen()
    game = Game()
    game.game_loop()
    pygame.quit()

