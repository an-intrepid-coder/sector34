from random import randrange, randint, choice
from constants import *
import pygame
from faction_type import FactionType, faction_type_to_color
from utility import d10000, d20, d100, coin_flip

class BattleSprite:
    def __init__(self, battle, pos, faction_type, value, width, length, hit=False, explosion=False, retreating=False):
        self.pos = pos
        self.faction_type = faction_type
        self.value = value
        self.explosion = explosion
        self.retreating = retreating
        self.width = width
        self.length = length
        self.speed = BASE_TACTICAL_SPEED_PX + randint(0, 1)
        self.battle = battle
        self.move_ticker = randrange(0, 100)
        self.laser_ticker = randrange(0, DESTROYER_LASER_FREQUENCY)
        self.hit = hit

    def fire_laser(self, surface):
        if self.laser_ticker == DESTROYER_LASER_FREQUENCY and not self.explosion:
            self.laser_ticker = 0
            for _ in range(DESTROYER_LASER_QUANTITY):
                if self.faction_type == FactionType.PLAYER:
                    color = "green"
                else:
                    color = "red"
                target = None
                if self.faction_type == self.battle.attacker_faction:
                    if len(self.battle.defender_sprites) > 0:
                        target = choice(self.battle.defender_sprites)
                elif self.faction_type == self.battle.defender_faction:
                    if len(self.battle.attacker_sprites) > 0:
                        target = choice(self.battle.attacker_sprites)
                if target is not None:
                    if not target.explosion:
                        target.hit = True
                        pygame.draw.line(surface, color, self.pos, target.pos, LASER_WIDTH)
        self.laser_ticker += 1

def random_destroyer_shape():
    return choice([DESTROYER_SHAPE_1, DESTROYER_SHAPE_2])

# TODO: More possible destroyer shapes

class Destroyer(BattleSprite): # TODO: More ship types
    def __init__(self, battle, pos, faction_type):
        super().__init__(battle, pos, faction_type, DESTROYER_VALUE, DESTROYER_WIDTH, DESTROYER_LENGTH)
        self.upscaled = False
        if d100()[0] <= DESTROYER_UPSCALE_CHANCE_OUT_OF_100:
            self.upscaled = True 
        self.sprite_pos = (self.pos[0] - self.length // 2, self.pos[1] - self.width // 2, self.length, self.width)
        # Base Surface
        self.surface = pygame.Surface((self.length, self.width))
        self.surface.set_colorkey(COLOR_ALPHA_KEY)
        self.surface.fill(COLOR_ALPHA_KEY)  
        shape = random_destroyer_shape()
        pygame.draw.polygon(self.surface, COLOR_DESTROYER, shape)
        pygame.draw.polygon(self.surface, "black", shape, 1) 
        self.frames = [] 
        self.frame_index = 0
        # Dots and racing stripes
        insignia_color = faction_type_to_color(self.faction_type)
        x = self.length // 8
        insignia_pos = (x * 6, self.width / 2)
        insignia_pos_2 = (x, insignia_pos[1])
        stripe_start = (x, insignia_pos[1])
        stripe_end = (insignia_pos[0] - (INSIGNIA_RADIUS + 2), insignia_pos[1])
        pygame.draw.line(self.surface, insignia_color, stripe_start, stripe_end)
        pygame.draw.circle(self.surface, insignia_color, insignia_pos, INSIGNIA_RADIUS)
        pygame.draw.circle(self.surface, "black", insignia_pos, INSIGNIA_RADIUS + 1, 1)
        pygame.draw.circle(self.surface, insignia_color, insignia_pos_2, INSIGNIA_RADIUS)
        pygame.draw.circle(self.surface, "black", insignia_pos_2, INSIGNIA_RADIUS + 1, 1)
        # Insert engine frames
        engine_frame_1 = self.surface.copy()
        pygame.draw.rect(engine_frame_1, ENGINE_COLOR_1, ENGINE_GLOW_RECT)
        self.frames.append(engine_frame_1)
        engine_frame_2 = self.surface.copy()
        pygame.draw.rect(engine_frame_2, ENGINE_COLOR_2, ENGINE_GLOW_RECT)
        self.frames.append(engine_frame_2)
        # Explosion frames 
        self.explosion_frames = [] 
        self.explosion_frame_index = 0
        for frame in range(NUM_EXPLOSION_FRAMES):
            explosion_frame = choice(self.frames).copy()
            for mark in range(NUM_EXPLOSION_MARKS):
                x = randrange(0, self.length)
                y = randrange(0, self.width)
                radius = randint(1, 2)
                color = choice([ENGINE_COLOR_1, ENGINE_COLOR_2])
                pygame.draw.circle(explosion_frame, color, (x, y), radius)
            self.explosion_frames.append(explosion_frame)
        # TODO: Maybe laser sprites instead of drawing the lasers in battles. Soon-ish. That'll look cool af.

    def draw(self, surface):
        retreat_rounds = self.battle.round >= len(self.battle.rounds) // 2
        if self.explosion: 
            frame = self.explosion_frames[self.explosion_frame_index]
            if self.upscaled:
                frame = pygame.transform.scale2x(frame)
            if d10000()[0] <= TACTICAL_BATTLE_CRITICAL_EXPLOSION_CHANCE_OUT_OF_10000:
                radius = EXPLOSION_RADIUS
                pygame.draw.circle(surface, COLOR_EXPLOSION, self.pos, radius)
                if self.faction_type == self.battle.attacker_faction:
                    self.battle.attacker_sprites.remove(self)
                elif self.faction_type == self.battle.defender_faction:
                    self.battle.defender_sprites.remove(self)
            else:
                if self.faction_type == self.battle.defender_faction:
                    flipped = pygame.transform.flip(frame, True, False)
                    surface.blit(flipped, self.sprite_pos)
                elif self.faction_type == self.battle.attacker_faction and retreat_rounds and self.battle.retreat:
                    flipped = pygame.transform.flip(frame, True, False)
                    surface.blit(flipped, self.sprite_pos)
                else:
                    surface.blit(frame, self.sprite_pos)
                self.explosion_frame_index = (self.explosion_frame_index + 1) % NUM_EXPLOSION_FRAMES
        else:
            frame = self.frames[self.frame_index]
            if self.upscaled:
                frame = pygame.transform.scale2x(frame)
            if self.faction_type == self.battle.defender_faction:
                    flipped = pygame.transform.flip(frame, True, False)
                    surface.blit(flipped, self.sprite_pos)
            elif retreat_rounds and self.battle.retreat and self.faction_type == self.battle.attacker_faction and not self.explosion:
                    flipped = pygame.transform.flip(frame, True, False)
                    surface.blit(flipped, self.sprite_pos)
            else:
                surface.blit(frame, self.sprite_pos)
            self.frame_index = (self.frame_index + 1) % NUM_ENGINE_FRAMES

    def move(self): 
        if self.move_ticker % MOVE_FREQUENCY == 0:
            retreat_rounds = self.battle.round >= len(self.battle.rounds) // 2
            end_rounds = self.battle.round >= len(self.battle.rounds)
            delta = self.speed
            if self.faction_type == self.battle.defender_faction:
                delta *= -1
            if self.battle.retreat and retreat_rounds and self.faction_type == self.battle.attacker_faction:
                delta *= -1
            new_x = self.pos[0] + delta
            if self.faction_type == self.battle.attacker_faction:
                winner = self.battle.winner == self.faction_type
                limit = new_x > SCREEN_WIDTH_PX / 2 - self.length * 2
                if limit and not (winner and end_rounds):
                    new_x = self.pos[0]
            elif self.faction_type == self.battle.defender_faction:
                limit = new_x < SCREEN_WIDTH_PX / 2 + self.length * 2
                if limit and not (self.battle.retreat and retreat_rounds):
                    new_x = self.pos[0]
            self.pos = (new_x, self.pos[1])
            self.sprite_pos = (self.pos[0] - self.length // 2, self.pos[1] - self.width // 2, self.length, self.width)
        self.move_ticker = (self.move_ticker + 1) % 100

class TacticalBattle:
    def __init__(self, fleet, location, attacker_faction, defender_faction, attacker_ships, defender_ships):
        self.attacker_faction = attacker_faction
        self.defender_faction = defender_faction
        self.attacker_ships = attacker_ships
        self.defender_ships = defender_ships
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

        # place destroyers (for now, all ships are destroyers)
        num_destroyers_attacker = self.attacker_ships
        num_destroyers_defender = self.defender_ships
        for _ in range(num_destroyers_attacker):
            x = randrange(TACTICAL_SCREEN_PADDING_PX, SCREEN_WIDTH_PX // 3 - TACTICAL_SCREEN_PADDING_PX)
            y = randrange(TACTICAL_SCREEN_PADDING_PX, SCREEN_HEIGHT_PX - TACTICAL_SCREEN_PADDING_PX)
            self.attacker_sprites.append(Destroyer(self, (x, y), self.attacker_faction))

        for _ in range(num_destroyers_defender):
            x = randrange(int(SCREEN_WIDTH_PX * .66), SCREEN_WIDTH_PX - TACTICAL_SCREEN_PADDING_PX)
            y = randrange(TACTICAL_SCREEN_PADDING_PX, SCREEN_HEIGHT_PX - TACTICAL_SCREEN_PADDING_PX)
            self.defender_sprites.append(Destroyer(self, (x, y), self.defender_faction))

    def is_close_battle(self):
        if self.attacker_ships == self.defender_ships:
            return True
        more = max(self.attacker_ships, self.defender_ships)
        less = min(self.attacker_ships, self.defender_ships)
        diff = more - less
        if diff < CLOSE_BATTLE_SHIP_DIFF:
            return True
        # I should make a note of this formula when I nail it. It'll be useful for other things
        return less + (less * CLOSE_BATTLE_SHIP_FACTOR) >= more  # oooh maybe

