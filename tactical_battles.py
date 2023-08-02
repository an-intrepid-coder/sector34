from random import randrange, randint, choice
from constants import *
import pygame
from faction_type import FactionType, faction_type_to_color
from utility import d10000, d20, d100, coin_flip, xthify
from battle_sprite import Destroyer

class TacticalBattle: 
    def __init__(self, sprite_list, fleet, location, attacker_faction, defender_faction, attacker_ships, defender_ships):
        self.attacker_faction = attacker_faction
        self.defender_faction = defender_faction
        self.attacker_ships = attacker_ships
        self.remaining_attacker_ships = attacker_ships
        self.defender_ships = defender_ships
        self.remaining_defender_ships = defender_ships
        self.retreat = False
        self.round = 0
        self.rounds = []
        self.starfield = None
        self.damage_due_attackers = 0
        self.damage_due_defenders = 0
        self.attacker_sprites = []
        self.defender_sprites = []
        self.winner = None
        self.fleet = fleet
        self.location = location
        self.last_stand = False
        self.charge = False
        self.battle_number = None
        self.prompt_text = None
        self.rolls = []
        self.roll_text = None
        self.brilliancies = []
        self.outnumber_die = []

        # place destroyers (for now, all ships are destroyers)
        num_destroyers_attacker = self.attacker_ships
        num_destroyers_defender = self.defender_ships
        for _ in range(num_destroyers_attacker):
            x = randrange(TACTICAL_SCREEN_PADDING_PX, SCREEN_WIDTH_PX // 3 - TACTICAL_SCREEN_PADDING_PX)
            y = randrange(TACTICAL_SCREEN_PADDING_PX, SCREEN_HEIGHT_PX - TACTICAL_SCREEN_PADDING_PX)
            upscaled = False
            if d100()[0] <= DESTROYER_UPSCALE_CHANCE_OUT_OF_100: 
                upscaled = True 

            self.attacker_sprites.append(Destroyer(self, choice(sprite_list[attacker_faction]), upscaled, (x, y), attacker_faction)) 

        for _ in range(num_destroyers_defender):
            x = randrange(int(SCREEN_WIDTH_PX * .66), SCREEN_WIDTH_PX - TACTICAL_SCREEN_PADDING_PX)
            y = randrange(TACTICAL_SCREEN_PADDING_PX, SCREEN_HEIGHT_PX - TACTICAL_SCREEN_PADDING_PX)
            upscaled = False
            if d100()[0] <= DESTROYER_UPSCALE_CHANCE_OUT_OF_100: 
                upscaled = True 
            self.defender_sprites.append(Destroyer(self, choice(sprite_list[defender_faction]), upscaled, (x, y), defender_faction)) 

    def update_roll_text(self, attacker_faction_name, defender_faction_name):
        font = pygame.font.Font(FONT_PATH, TACTICAL_ROLLS_FONT_SIZE)
        attacker_rolls = self.rolls[self.round]["attacker_rolls"]
        defender_rolls = self.rolls[self.round]["defender_rolls"]
        attacker_roll_text = "{}: {}".format(attacker_faction_name, attacker_rolls)
        if self.charge:
            attacker_roll_text += " (+{} from 'Charge!')".format(CHARGE_D20_BONUS)
        if self.brilliancies[self.round]["attacker"]:
            attacker_roll_text += " (+{} from Brilliancy)".format(BRILLIANCY_BONUS)
        if self.outnumber_die[self.round]["attacker"] > 0:
            attacker_roll_text += " ({} bonus dice)".format(self.outnumber_die[self.round]["attacker"])
        defender_roll_text = "{}: {}".format(defender_faction_name, defender_rolls)
        if self.last_stand:
            defender_roll_text += " (+{} from 'Last Stand!')".format(LAST_STAND_D20_BONUS)
        if self.brilliancies[self.round]["defender"]:
            defender_roll_text += " (+{} from Brilliancy)".format(BRILLIANCY_BONUS)
        if self.outnumber_die[self.round]["defender"] > 0:
            defender_roll_text += " ({} bonus dice)".format(self.outnumber_die[self.round]["defender"])
        self.roll_text = font.render("(round #{})   {}      {}".format(self.round + 1, attacker_roll_text, defender_roll_text), True, COLOR_SENSOR, "black")

    def update_prompt_text(self, attacker_faction_name, defender_faction_name):
        font = pygame.font.Font(FONT_PATH, TACTICAL_MODE_FONT_SIZE)
        self.prompt_text = font.render("{} ({} ships) vs {} ({} ships) <{} battle of {}> <SPACE to skip battle>".format(attacker_faction_name, self.remaining_attacker_ships, defender_faction_name, self.remaining_defender_ships, xthify(self.battle_number + 1), self.location.name), True, COLOR_SENSOR, "black")

    def is_close_battle(self):
        if self.attacker_ships == self.defender_ships:
            return True
        more = max(self.attacker_ships, self.defender_ships)
        less = min(self.attacker_ships, self.defender_ships)
        diff = more - less
        if diff < CLOSE_BATTLE_SHIP_DIFF:
            return True
        return less + (less * CLOSE_BATTLE_SHIP_FACTOR) >= more  

