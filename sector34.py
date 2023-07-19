import pygame
from pygame.locals import *
from constants import *
from tactical_battles import TacticalBattle
from star_map import StarMap
from location import LocationType, generate_starfield
from clickable import Clickable
from faction import Faction
from faction_type import FactionType, faction_type_to_color, ai_empire_faction_types
from fleet import Fleet
from console import ConsoleLog
from utility import d20, d100
from pygame.math import Vector2
from random import shuffle, randint, choice
from math import ceil


class Game:
    def __init__(self):
        self.debug_mode = False
        self.watch_mode = False
        self.watch_timer = 0
        self.screen = pygame.display.get_surface()
        self.display_changed = False
        self.clock = pygame.time.Clock()
        self.running = True
        self.star_map = StarMap(self.debug_mode)
        self.hard_mode = False

        self.ai_factions = []
        for fac in ai_empire_faction_types:
            ai_faction = Faction(fac, self.star_map)
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

        def victory_splash():
            # placeholder
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

        # Checks the victory condition (currently control of a certain % of the
        # map and the elimination of all Pirates and AI Empire factions).
        def victory_check():
            num_pirate_systems = len(
                [i for i in filter(lambda x: x.faction_type == FactionType.PIRATES, self.star_map.locations)])
            num_ai_empire_systems = len(
                [i for i in filter(lambda x: x.faction_type in ai_empire_faction_types, self.star_map.locations)])
            num_player_systems = len(
                [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.star_map.locations)])
            conquest_percent = num_player_systems / self.star_map.num_stars * 100
            self.conquest_percent = conquest_percent
            if num_pirate_systems == 0 and not self.all_pirates_destroyed:
                self.console.push("All Pirates in the sector have been brought under control...")
                self.all_pirates_destroyed = True
            if num_ai_empire_systems == 0 and not self.all_ai_empires_destroyed:
                self.console.push("All rival successors to the empire have been vanquished...")
                self.all_ai_empires_destroyed = True
            if num_pirate_systems == 0 == num_ai_empire_systems and conquest_percent >= CONQUEST_PERCENT_FOR_VICTORY:
                self.console.push("")
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
                fac.run_behavior(self)

        # Moves any fleets
        def update_fleets():
            for fleet in self.star_map.deployed_fleets:
                fleet.move()

        # Each system has a random chance to spawn reenforcements.
        # Player reenforcements go to a common pool, while
        # AI reenforcements remain local (for now).
        def spawn_reenforcements():
            for loc in self.star_map.locations:
                if loc.will_spawn_reenforcements(self.hard_mode):
                    if loc.faction_type == FactionType.PLAYER:
                        self.player_reenforcement_pool += 1
                    else:
                        loc.ships += 1

        # Finds any two fleets of opposing factions
        # at the same location, and resolves combats.
        # For now, there are no deep space interceptions
        # Friendly arrivals disembark at the destination
        def resolve_fleet_arrivals():
            for fleet in self.star_map.deployed_fleets:
                for loc in self.star_map.locations:
                    # Handle fleets bringing reenforcements to a system:
                    if fleet.pos == fleet.destination.pos == loc.pos and fleet.faction_type == loc.faction_type and fleet.faction_type != FactionType.PIRATES:
                        loc.ships += fleet.ships
                        if fleet is self.selected_fleet:
                            self.selected_fleet = None
                        self.star_map.remove_fleet(fleet)
                        # Handle fleets entering combat in a system:
                    elif fleet.pos == fleet.destination.pos == loc.pos and (
                            fleet.faction_type == FactionType.PIRATES or fleet.faction_type != loc.faction_type):
                        # A combat begins
                        attackers = fleet.ships
                        attacker_faction = fleet.faction_type
                        attacker_name = fleet.name
                        defenders = loc.ships
                        defender_faction = loc.faction_type
                        fighting = True
                        retreating = False
                        attackers_won = False
                        defenders_won = False
                        attackers_losses = 0
                        defenders_losses = 0
                        rounds = 1
                        tactical_battle = TacticalBattle(loc, attacker_faction, defender_faction, attackers, defenders)
                        tactical_battle.starfield = loc.starfield
                        last_stand = False
                        if attackers > defenders and d100()[0] <= LAST_STAND_CHANCE_OUT_OF_100:
                            last_stand = True
                            tactical_battle.last_stand = True
                        charge = False
                        if defenders > attackers and d100()[0] <= CHARGE_CHANCE_OUT_OF_100:
                            charge = True
                            tactical_battle.charge = True
                        while fighting:
                            attacker_round_losses = 0
                            defender_round_losses = 0
                            attacker_bonus = 0
                            if charge:
                                attacker_bonus += CHARGE_D20_BONUS
                            if d100()[0] <= BRILLIANCY_CHANCE_OUT_OF_100:
                                attacker_bonus += BRILLIANCY_BONUS
                            defender_bonus = 0
                            if last_stand:
                                defender_bonus += LAST_STAND_D20_BONUS
                            if d100()[0] <= BRILLIANCY_CHANCE_OUT_OF_100:
                                defender_bonus += BRILLIANCY_BONUS
                            # victory check
                            if attackers <= 0 or defenders <= 0:
                                break
                            # calculate fleet widths and bonuses
                            if attackers > defenders:
                                outnumber_margin = int((attackers - defenders) / (defenders * DEFAULT_OUTNUMBER_MARGIN))
                                attackers_width = DEFAULT_FLEET_WIDTH + outnumber_margin
                                defenders_width = DEFAULT_FLEET_WIDTH
                            elif attackers < defenders:
                                attackers_width = DEFAULT_FLEET_WIDTH
                                outnumber_margin = int((defenders - attackers) / (attackers * DEFAULT_OUTNUMBER_MARGIN))
                                defenders_width = DEFAULT_FLEET_WIDTH + outnumber_margin
                            else:
                                attackers_width = DEFAULT_FLEET_WIDTH
                                defenders_width = DEFAULT_FLEET_WIDTH
                            if attackers < DEFAULT_FLEET_WIDTH:
                                attackers_width = attackers
                            if defenders < DEFAULT_FLEET_WIDTH:
                                defenders_width = defenders
                            if attackers > defenders:
                                measure_width = defenders_width
                            elif attackers < defenders:
                                measure_width = attackers_width
                            else:
                                measure_width = attackers_width

                            # roll for attackers and defenders
                            attackers_roll = d20(num_dice=attackers_width, bonus=attacker_bonus)
                            defenders_roll = d20(num_dice=defenders_width, bonus=defender_bonus)
                            for die in range(measure_width):
                                if attackers_roll[die] > defenders_roll[die]:
                                    defenders -= 1
                                    defenders_losses += 1
                                    defender_round_losses += 1
                                else:  # defenders win ties for now
                                    attackers -= 1
                                    attackers_losses += 1
                                    attacker_round_losses += 1

                            # calculate retreat chance for attackers
                            if rounds > 1 and attackers > 0 and not charge:
                                if attackers < defenders:
                                    outnumber_margin = (defenders - attackers) // (attackers * DEFAULT_OUTNUMBER_MARGIN)
                                    retreat_chance_out_of_100 = DEFAULT_RETREAT_CHANCE_OUT_OF_100 * outnumber_margin
                                    if retreat_chance_out_of_100 > DEFAULT_RETREAT_CHANCE_HARD_CAP:
                                        retreat_chance_out_of_100 = DEFAULT_RETREAT_CHANCE_HARD_CAP
                                    if d100()[0] <= retreat_chance_out_of_100:
                                        nearest_place_to_flee = self.star_map.nearest_friendly_world_to(fleet)
                                        # If there is nowhere left to retreat to, they'll fight to the death
                                        if nearest_place_to_flee is not None:
                                            if nearest_place_to_flee.ly_to(fleet.pos) <= DEFAULT_FUEL_RANGE_LY:
                                                fighting = False
                                                retreating = True
                                                tactical_battle.retreat = True

                            tactical_battle.rounds.append(
                                {"attacker_losses": attacker_round_losses, "defender_losses": defender_round_losses})

                            rounds += 1

                        # Handle the effects of the battle
                        if attackers > 0 >= defenders:
                            tactical_battle.winner = attacker_faction
                            loc.faction_type = fleet.faction_type
                            loc.ships = attackers
                            if fleet == self.selected_fleet:
                                self.selected_fleet = None
                            self.star_map.remove_fleet(fleet)
                            attackers_won = True
                            if attacker_faction == FactionType.PIRATES:
                                self.all_pirates_destroyed = False
                        elif attackers <= 0:
                            tactical_battle.winner = defender_faction
                            loc.ships = defenders
                            if fleet == self.selected_fleet:
                                self.selected_fleet = None
                            self.star_map.remove_fleet(fleet)
                            defenders_won = True
                            if defender_faction == FactionType.PIRATES:
                                self.all_pirates_destroyed = False

                        # Handle retreats
                        if retreating:
                            tactical_battle.winner = defender_faction
                            loc.ships = defenders
                            fleet.ships = attackers
                            defenders_won = True
                            retreating_to = self.star_map.nearest_friendly_world_to(fleet)
                            if fleet.faction_type == FactionType.PIRATES:
                                retreating_to = self.star_map.nearest_vulnerable_world_to(fleet)
                            if retreating_to is None:
                                self.star_map.remove_fleet(fleet)
                                retreating = False
                            else:
                                fleet.destination = retreating_to

                        # Handle output if player involved or can witness
                        if attacker_faction == FactionType.PLAYER or defender_faction == FactionType.PLAYER:
                            self.tactical_battles.append(tactical_battle)
                            if attackers_won:
                                faction_name = self.star_map.faction_names[loc.faction_type]
                                self.console.push(
                                    "{} of {} conquered {} (losses: {} atk / {} def, {} rounds)".format(attacker_name,
                                                                                                        faction_name,
                                                                                                        loc.name,
                                                                                                        attackers_losses,
                                                                                                        defenders_losses,
                                                                                                        rounds))
                                if attacker_faction == FactionType.PLAYER:
                                    self.battles_won += 1
                                    self.ships_destroyed += defenders_losses
                                    self.ships_lost += attackers_losses
                                else:
                                    self.battles_lost += 1
                                    self.ships_destroyed += defenders_losses
                                    self.ships_lost += attackers_losses

                            elif defenders_won:
                                faction_name = self.star_map.faction_names[attacker_faction]
                                if defender_faction == FactionType.PLAYER:
                                    self.battles_won += 1
                                    self.ships_destroyed += attackers_losses
                                    self.ships_lost += defenders_losses
                                else:
                                    self.battles_lost += 1
                                    self.ships_destroyed += attackers_losses
                                    self.ships_lost += defenders_losses
                                if retreating:
                                    self.console.push(
                                        "defenders of {} caused {} from {} to retreat (losses: {} atk / {} def; {} rounds)".format(
                                            loc.name, fleet.name, faction_name, attackers_losses,
                                            defenders_losses, rounds))
                                else:
                                    self.console.push(
                                        "defenders of {} destroyed {} from {} (losses: {} atk / {} def; {} rounds)".format(
                                            loc.name, attacker_name, faction_name, attackers_losses,
                                            defenders_losses, rounds))

        def check_end_turn_clicks(pos):  
            if self.end_turn_button.clicked(pos):
                self.turn_processing_mode = True
                self.display_changed = True

        # Check if any locations have been clicked on:
        def check_location_clicks(pos):
            for loc in self.star_map.locations:
                if loc.clicked(pos):
                    if self.deploy_mode and self.deploy_amount > 0:
                        if not loc.pos == self.selected_system.pos:
                            distance = Vector2(loc.pos).distance_to(self.selected_system.pos) / LY
                            if distance <= DEFAULT_FUEL_RANGE_LY:
                                self.console.push(
                                    "Deploying fleet of {} ships to {}".format(self.deploy_amount, loc.name))
                                name = self.star_map.name_a_fleet(self.selected_system.faction_type)
                                new_fleet = Fleet(name, self.selected_system.pos, self.selected_system.faction_type,
                                                  self.deploy_amount, loc)
                                self.selected_system.ships -= self.deploy_amount
                                self.star_map.deployed_fleets.append(new_fleet)
                                self.selected_fleet = new_fleet
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
                            loc.ships += self.reenforce_amount
                            self.reenforce_amount = 0
                            self.reenforce_mode = False
                            self.display_changed = True
                    elif loc.pos != self.selected_system.pos and (player_can_see(loc.pos) or self.debug_mode):
                        self.selected_system = loc
                        self.deploy_amount = 0
                        self.display_changed = True
                        break

        def check_reenforce_button_clicks(pos, shift, ctrl):
            if self.reenforce_button.clicked(pos) and self.reenforce_amount > 0:
                self.console.push("REENFORCE MODE: Select target")
                self.reenforce_mode = True
                self.display_changed = True
            elif self.reenforce_up_button.clicked(pos):
                if not (shift or ctrl) and self.reenforce_amount < self.player_reenforcement_pool:
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

        def check_deploy_button_clicks(pos, shift, ctrl):
            if self.deploy_button.clicked(pos) and self.selected_system.faction_type == FactionType.PLAYER:
                self.console.push("DEPLOY MODE: Select target")
                self.deploy_mode = True
                self.display_changed = True
                self.can_deploy_to = [i for i in filter(lambda x: x.ly_to(self.selected_system.pos) <= DEFAULT_FUEL_RANGE_LY, self.star_map.locations)]

            elif self.deploy_up_button.clicked(pos) and self.selected_system.faction_type == FactionType.PLAYER:
                if not (shift or ctrl) and self.deploy_amount < self.selected_system.ships - 1:
                    self.deploy_amount += 1
                    self.display_changed = True
                elif shift and self.deploy_amount + 10 < self.selected_system.ships - 1:
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
            for fleet in self.star_map.deployed_fleets:
                if fleet.clicked(pos) and (player_can_see(pos) or self.debug_mode):
                    # TODO: Toggle between fleets on same loc. For now, only displays first encountered
                    self.selected_fleet = fleet
                    self.display_changed = True
                    break

        def draw_eta_line():  
            # Display ETA line
            color = COLOR_SENSOR
            pygame.draw.line(self.screen, color, self.selected_system.pos, self.eta_line_target.pos,
                             FLEET_ETA_LINE_WIDTH)
            eta = ceil(self.selected_system.ly_to(self.eta_line_target.pos) / DEFAULT_SPEED_LY)
            text = "{} TURNS".format(eta)
            font = pygame.font.Font(FONT_PATH, ETA_LINE_FONT_SIZE)
            surface = font.render(text, True, COLOR_FUEL_RANGE)
            pos = (self.eta_line_target.pos[0], self.eta_line_target.pos[1] - surface.get_height())
            self.screen.blit(surface, pos)

        def draw_incoming_fleets_overlay(): 
            for fleet in self.star_map.deployed_fleets:
                if fleet.faction_type != FactionType.PLAYER:
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
                pygame.draw.rect(map_surface, "blue", (0, 0, MAP_WIDTH_PX, MAP_HEIGHT_PX), 1)
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

                # display star systems and garrisoned fleets:
                font = pygame.font.Font(FONT_PATH, STAR_SYSTEM_FONT_SIZE)
                for loc in self.star_map.locations:
                    if loc.locationType == LocationType.STAR_SYSTEM:
                        if loc.in_sensor_view:
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
                            pygame.draw.circle(map_surface, "white", loc.pos, STAR_RADIUS_PX)

                # display deployed fleets:
                for fleet in self.star_map.deployed_fleets:
                    if fleet.in_sensor_view:
                        pygame.draw.line(map_surface, (200, 200, 255), fleet.pos, fleet.destination.pos)
                        top = (fleet.pos[0], fleet.pos[1] - STAR_RADIUS_PX)
                        bottom = (fleet.pos[0], fleet.pos[1] + STAR_RADIUS_PX)
                        right = (fleet.pos[0] + STAR_RADIUS_PX, fleet.pos[1])
                        left = (fleet.pos[0] - STAR_RADIUS_PX, fleet.pos[1])
                        pygame.draw.polygon(map_surface, faction_type_to_color(fleet.faction_type), (top, right, bottom, left), 1)
                        fleet_size_text = font.render("{}".format(fleet.ships), True, "white")
                        pos = (
                            fleet.pos[0] - fleet_size_text.get_width() / 2,
                            fleet.pos[1] - fleet_size_text.get_height() / 2)
                        map_surface.blit(fleet_size_text, pos)

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
                    selected_system_local_fleets_text = "Local Fleets: {}".format(self.selected_system.ships)

                # TODO: System bonuses and peculiarities/modifiers

                selected_system_text_surface = font.render(selected_system_text, True, "green")
                hud_surface.blit(selected_system_text_surface, (0, HUD_FONT_SIZE + 1))

                selected_system_owner_surface = font.render(selected_system_owner_text, True, "green")
                hud_surface.blit(selected_system_owner_surface, (0, (HUD_FONT_SIZE + 1) * 2))

                selected_system_local_fleets_surface = font.render(selected_system_local_fleets_text, True, "green")
                hud_surface.blit(selected_system_local_fleets_surface, (0, (HUD_FONT_SIZE + 1) * 3))

                if self.selected_system.faction_type == FactionType.PLAYER:
                    # Deploy button
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
                    selected_fleet_size_text = "Fleet Size: {}".format(self.selected_fleet.ships)
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

                vic_empires = font.render("All Empires Defeated", True, "green")
                hud_surface.blit(vic_empires, (0, (HUD_FONT_SIZE + 1) * 24))
                rect = (HUD_WIDTH_PX - HUD_CHECKBOX_WIDTH - 10, (HUD_FONT_SIZE + 1) * 24, HUD_CHECKBOX_WIDTH, HUD_FONT_SIZE)
                pygame.draw.rect(hud_surface, "green", rect, 1)
                if self.all_ai_empires_destroyed:
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
                for line in range(lines):
                    index = last - line
                    if index >= 0:
                        msgs.append(self.console.messages[index])

                msgs.reverse()
                for line in range(len(msgs)):
                    line_surface = font.render(msgs[line], True, "green")
                    console_surface.blit(line_surface, (0, line * line_height))

                self.screen.blit(console_surface, (0, MAP_HEIGHT_PX))

            # clear display
            self.screen.fill("white")

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
                draw_eta_line() 

            if self.incoming_fleets_overlay_mode:
                draw_incoming_fleets_overlay()  

            if self.outgoing_fleets_overlay_mode:
                draw_outgoing_fleets_overlay()  

            self.display_changed = False
            pygame.display.flip()

        def eta_line_check(pos): 
            found = False
            for loc in self.can_deploy_to: 
                if loc is not self.selected_system:
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
                fleet = Fleet(self.star_map.name_a_fleet(FactionType.PIRATES), pos, FactionType.PIRATES, num_ships, target)
                self.star_map.deployed_fleets.append(fleet)

        def strategic_mode():
            # handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    # quit game:
                    self.running = False
                elif event.type == MOUSEBUTTONUP and not self.turn_processing_mode:
                    # Mouse clicks
                    shift = pygame.key.get_pressed()[K_LSHIFT] or pygame.key.get_pressed()[K_RSHIFT]
                    ctrl = pygame.key.get_pressed()[K_LCTRL] or pygame.key.get_pressed()[K_RCTRL]
                    pos = pygame.mouse.get_pos()
                    check_location_clicks(pos)
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
                    if pygame.key.get_pressed()[K_SPACE]:
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
                    elif pygame.key.get_pressed()[K_b] and shift and ctrl:
                        self.skipping_tactical_battles = not self.skipping_tactical_battles
                        self.console.push("Skipping Tactical Battles: {}".format(self.skipping_tactical_battles))
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_w] and shift and ctrl:
                        self.watch_mode = not self.watch_mode
                        self.console.push("Watch Mode: {}".format(self.watch_mode))
                        self.display_changed = True
                        if self.watch_mode and FactionType.PLAYER not in self.ai_factions:
                            self.ai_factions.append(Faction(FactionType.PLAYER, self.star_map))
                        elif not self.watch_mode and FactionType.PLAYER in self.ai_factions:
                            self.ai_factions = [i for i in filter(lambda x: x.faction_type == FactionType.PLAYER, self.ai_factions)]
                            self.watch_timer = 0
                    elif pygame.key.get_pressed()[K_d] and shift and ctrl:
                        self.debug_mode = not self.debug_mode
                        self.console.push("Debug Mode: {}".format(self.debug_mode))
                        self.display_changed = True
                    elif pygame.key.get_pressed()[K_h] and shift and ctrl:
                        self.hard_mode = not self.hard_mode
                        self.console.push("Hard Mode: {}".format(self.hard_mode))
                        self.display_changed = True
                elif event.type == MOUSEMOTION and not self.turn_processing_mode:
                    rel = pygame.mouse.get_rel()
                    if rel != (0, 0): # Avoid "very small" mouse movement detection distances
                        pos = pygame.mouse.get_pos()
                        # ETA Line Hover Checks
                        if self.deploy_mode:
                            eta_line_check(pos)
                            self.mouse_last = pos  
                        # Additional strat-mode hover logic TODO
            
            # Handle processing between turns
            game_on = not (self.game_over_mode or self.victory_mode)
            if self.turn_processing_mode and game_on:
                draw_processing_blurb()
                off_map_pirate_raid_check() # TODO
                update_fleets()
                resolve_fleet_arrivals()
                spawn_reenforcements()
                run_ai_behavior()
                game_over_check()
                victory_check()
                self.turn += 1
                self.deploy_amount = 0
                self.reenforce_amount = 0
                self.turn_processing_mode = False
                self.display_changed = True

            # Draw main display if it has changed
            if self.display_changed:
                draw_display()   

        def tactical_mode():
            battle = self.tactical_battles[0]
            attacker_faction_name = self.star_map.faction_names[battle.attacker_faction]
            defender_faction_name = self.star_map.faction_names[battle.defender_faction]
            font = pygame.font.Font(FONT_PATH, TACTICAL_MODE_FONT_SIZE)
            prompt_text = font.render("{} ({} ships) vs {} ({} ships) at {}  | <SPACE to skip battle>".format(attacker_faction_name, battle.attacker_ships, defender_faction_name, battle.defender_ships, battle.location.name), True, "green", "black")
            end_font = pygame.font.Font(FONT_PATH, TACTICAL_BATTLE_RESULT_FONT_SIZE)
            if battle.attacker_faction == battle.winner:
                victory_text = end_font.render("{} lost fleet defending {}".format(defender_faction_name, battle.location.name), True, "green", "black")
            elif battle.retreat:
                victory_text = end_font.render("Fleet from {} retreats in defeat from {}.".format(attacker_faction_name, battle.location.name), True, "green", "black")
            else:
                victory_text = end_font.render("Fleet from {} destroyed assaulting {}".format(attacker_faction_name, battle.location.name), True, "green", "black")

            def draw_tactical_mode():
                self.screen.blit(battle.starfield, (0, 0))
                self.screen.blit(prompt_text, (7, 7))
                for sprite in battle.attacker_sprites:
                    sprite.draw(self.screen) 
                    sprite.fire_laser(self.screen)  
                    sprite.move()  
                for sprite in battle.defender_sprites:
                    sprite.draw(self.screen)
                    sprite.fire_laser(self.screen)  
                    sprite.move()  
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
                    attacker_targets = [i for i in filter(lambda x: x.hit and not x.explosion, battle.attacker_sprites)]
                    while battle.damage_due_attackers > 0:
                        valid = [i for i in filter(lambda x: x.value <= battle.damage_due_attackers and not x.explosion,
                                                   attacker_targets)]
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

        def watch_mode_check():
            if self.watch_mode:
                self.watch_timer += 1
                if self.watch_timer == WATCH_TIMER_RATE:
                    self.watch_timer = 0
                    self.turn_processing_mode = True

        # Game loop
        self.display_changed = True
        draw_display()
        while self.running:
            watch_mode_check()
            if len(self.tactical_battles) == 0: 
                strategic_mode() 
            elif len(self.tactical_battles) > 0: 
                tactical_mode()
            pygame.event.pump() 
            self.clock.tick(FPS)

def loading_screen():
    screen = pygame.display.get_surface()
    bg = generate_starfield()
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
    pygame.mixer.quit()
    loading_screen()
    game = Game()
    game.game_loop()
    pygame.quit()

