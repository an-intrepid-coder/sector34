import pygame 
from constants import *
from faction_type import faction_type_to_color, FactionType
from random import choice, randrange, randint
from utility import d10000, d20, d100, coin_flip
from pygame.math import Vector2

class MissileSprite: 
    def __init__(self, ):
        self.surface = pygame.Surface((20, 20)) 
        self.surface.set_colorkey(COLOR_ALPHA_KEY)
        self.surface.fill(COLOR_ALPHA_KEY)  
        self.frames = []
        for _ in range(NUM_PULSE_FRAMES // 2):
            frame = self.surface.copy()  
            pygame.draw.circle(frame, "red", (20 // 2, 20 // 2), MISSILE_CORE_RADIUS_PX)
            self.frames.append(frame)
        for _ in range(NUM_PULSE_FRAMES // 2):
            frame = self.surface.copy()  
            pygame.draw.circle(frame, "red", (20 // 2, 20 // 2), MISSILE_CORE_RADIUS_PX)
            pygame.draw.circle(frame, "white", (20 // 2, 20 // 2), MISSILE_CORE_RADIUS_PX + MISSILE_CORE_PADDING_PX, MISSILE_CORE_PADDING_PX)
            self.frames.append(frame)

class MissileObject:
    def __init__(self, pos, sprite, target_sprite):
        self.velocity = 0 
        self.target = target_sprite
        self.sprite = sprite 
        self.pos = pos      
        self.arrived = False
        self.frames_index = 0

    def draw(self, surface):
        surface.blit(self.sprite.frames[self.frames_index], self.pos)
        self.frames_index = (self.frames_index + 1) % NUM_PULSE_FRAMES
        if self.target is not None:
            if self.target.pos == self.pos:
                self.target.hit = True  
                pygame.draw.circle(surface, COLOR_EXPLOSION, self.pos, MISSILE_CORE_RADIUS_PX * 3) 

    def update(self):
        self.velocity += 1 
        if self.target is not None:
            self.pos = Vector2(self.pos).move_towards(self.target.pos, self.velocity)
        if self.target is None:
            self.arrived = True 
        elif self.pos == self.target.pos:
            self.arrived = True

class BattleSprite:  
    def __init__(self, faction_type, shape):
        self.width = DESTROYER_WIDTH
        if faction_type != FactionType.EXOGALACTIC_INVASION:
            self.length = DESTROYER_LENGTH
        else:
            self.length = self.width
        self.faction_type = faction_type
        # Base Surface
        self.surface = pygame.Surface((self.length, self.width))
        self.surface.set_colorkey(COLOR_ALPHA_KEY)
        self.surface.fill(COLOR_ALPHA_KEY)  
        if faction_type != FactionType.EXOGALACTIC_INVASION:
            pygame.draw.polygon(self.surface, COLOR_DESTROYER, shape)
            pygame.draw.polygon(self.surface, "black", shape, 1) 
        else:
            pos = (self.width / 2, self.length / 2) 
            pygame.draw.circle(self.surface, COLOR_DESTROYER, pos, self.width // 2 - 3)
            pygame.draw.circle(self.surface, "black", pos, self.width // 2 - 2, 1)
        self.frames = [] 
        # Dots and racing stripes
        insignia_color = faction_type_to_color(self.faction_type)
        if faction_type != FactionType.EXOGALACTIC_INVASION:
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
        else:
            pos = (self.width / 2, self.length / 2) 
            pygame.draw.circle(self.surface, COLOR_EXOGALACTIC_INVADERS, pos, INSIGNIA_RADIUS)
            pygame.draw.circle(self.surface, "black", pos, INSIGNIA_RADIUS + 1, 1)
        # Insert engine frames 
        engine_frame_1 = self.surface.copy() 
        if faction_type != FactionType.EXOGALACTIC_INVASION:
            pygame.draw.rect(engine_frame_1, ENGINE_COLOR_1, ENGINE_GLOW_RECT)
            self.frames.append(engine_frame_1)
        else:
            pos = (self.width / 2, self.length / 2) 
            pygame.draw.circle(engine_frame_1, ENGINE_COLOR_1, pos, self.width // 2 - 1, 1)
            for _ in range(INVADER_ENGINE_FRAMES): 
                self.frames.append(engine_frame_1)
        engine_frame_2 = self.surface.copy()
        if faction_type != FactionType.EXOGALACTIC_INVASION:
            pygame.draw.rect(engine_frame_2, ENGINE_COLOR_2, ENGINE_GLOW_RECT)
            self.frames.append(engine_frame_2)
        else:
            pos = (self.width / 2, self.length / 2) 
            pygame.draw.circle(engine_frame_2, ENGINE_COLOR_2, pos, self.width // 2 - 1, 1)
            for _ in range(INVADER_ENGINE_FRAMES):
                self.frames.append(engine_frame_2)
        # Explosion frames 
        self.explosion_frames = [] 
        for frame in range(NUM_EXPLOSION_FRAMES):
            explosion_frame = choice(self.frames).copy()
            for mark in range(NUM_EXPLOSION_MARKS):
                x = randrange(0, self.length)
                y = randrange(0, self.width)
                radius = randint(1, 2)
                color = choice([ENGINE_COLOR_1, ENGINE_COLOR_2])
                pygame.draw.circle(explosion_frame, color, (x, y), radius)
            self.explosion_frames.append(explosion_frame)

class Destroyer: 
    def __init__(self, battle, sprite, upscaled, pos, faction_type, hit=False, explosion=False, retreating=False):
        self.pos = pos
        self.faction_type = faction_type
        self.value = 1
        self.explosion = explosion
        self.retreating = retreating
        self.width = DESTROYER_WIDTH
        self.length = DESTROYER_LENGTH
        self.speed = BASE_TACTICAL_SPEED_PX + randint(0, 1)
        self.battle = battle
        self.move_ticker = randrange(0, 100)
        self.laser_ticker = randrange(0, DESTROYER_LASER_FREQUENCY)
        self.missile_ticker = randrange(0, MISSILE_TICKER_COUNT)
        self.hit = hit
        self.upscaled = upscaled
        self.sprite = sprite
        self.sprite_pos = (self.pos[0] - self.length // 2, self.pos[1] - self.width // 2, self.length, self.width)
        self.frame_index = randrange(0, len(sprite.frames))
        self.explosion_frame_index = randrange(0, len(sprite.explosion_frames))
        self.at_line = False

    def fire_laser(self, surface):
        ticker_limit = DESTROYER_LASER_FREQUENCY
        if self.at_line:
            ticker_limit = 30
        if self.laser_ticker >= ticker_limit and not self.explosion:
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
                        width = LASER_WIDTH
                        if self.at_line:
                            width = 1
                        pygame.draw.line(surface, color, self.pos, target.pos, width)
                        if not self.at_line:
                            pygame.draw.circle(surface, COLOR_EXPLOSION, target.pos, LASER_WIDTH * 2)  # testing
                            pygame.draw.circle(surface, color, self.pos, LASER_WIDTH * 2)  # testing
        self.laser_ticker += 1

    def draw(self, surface): 
        retreat_rounds = self.battle.round >= len(self.battle.rounds) // 2
        if self.explosion: 
            frame = self.sprite.explosion_frames[self.explosion_frame_index]
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
            frame = self.sprite.frames[self.frame_index]
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
            if self.faction_type != FactionType.EXOGALACTIC_INVASION:
                self.frame_index = (self.frame_index + 1) % NUM_ENGINE_FRAMES 
            else:
                self.frame_index = (self.frame_index + 1) % INVADER_ENGINE_FRAMES_TOTAL 

    def move(self): 
        if self.battle.round == len(self.battle.rounds) // 2:
            self.speed = 1 
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
                    self.at_line = True
            elif self.faction_type == self.battle.defender_faction:
                limit = new_x < SCREEN_WIDTH_PX / 2 + self.length * 2
                if limit and not (self.battle.retreat and retreat_rounds):
                    new_x = self.pos[0]
                    self.at_line = True
            self.pos = (new_x, self.pos[1])
            self.sprite_pos = (self.pos[0] - self.length // 2, self.pos[1] - self.width // 2, self.length, self.width)
        self.move_ticker = (self.move_ticker + 1) % 100

