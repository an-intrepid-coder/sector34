from random import randrange, randint, choice
from constants import *
import pygame
from faction import Faction


def generate_starfield():
    starfield_surface = pygame.Surface((SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX))
    num_stars = int((SCREEN_WIDTH_PX * SCREEN_HEIGHT_PX) * STARFIELD_DENSITY)
    for _ in range(num_stars):
        pos = (randrange(0, SCREEN_WIDTH_PX), randrange(0, SCREEN_HEIGHT_PX))
        radius = randint(1, 2)
        pygame.draw.circle(starfield_surface, "white", pos, radius)
    return starfield_surface


class BattleSprite:
    def __init__(self, battle, pos, faction, value, width, length, hit=False, explosion=False, retreating=False):
        self.pos = pos
        self.faction = faction
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
                if self.faction == Faction.PLAYER:
                    color = "green"
                else:
                    color = "red"
                target = None
                if self.faction == self.battle.attacker_faction:
                    target = choice(self.battle.defender_sprites)
                elif self.faction == self.battle.defender_faction:
                    target = choice(self.battle.attacker_sprites)
                target.hit = True
                pygame.draw.line(surface, color, self.pos, target.pos, 1)
        self.laser_ticker += 1

    def move(self):
        if not self.explosion:
            if self.move_ticker % MOVE_FREQUENCY == 0:
                delta = self.speed
                if self.faction == self.battle.defender_faction:
                    delta *= -1
                if self.battle.retreat and self.battle.round >= len(self.battle.rounds) // 2 and self.faction == self.battle.attacker_faction:
                    delta *= -1
                x = self.pos[0] + delta
                self.pos = (x, self.pos[1])
            self.move_ticker = (self.move_ticker + 1) % 100


class Destroyer(BattleSprite):
    def __init__(self, battle, pos, faction):
        super().__init__(battle, pos, faction, DESTROYER_VALUE, DESTROYER_WIDTH, DESTROYER_LENGTH)

    def draw(self, surface):
        rect = (self.pos[0] - self.length // 2, self.pos[1] - self.width // 2, self.length, self.width)
        pygame.draw.rect(surface, "gray", rect)
        if self.explosion:
            x = randrange(rect[0], rect[0] + rect[2])
            y = randrange(rect[1], rect[1] + rect[3])
            r = randrange(200, 256)
            g = randrange(0, 100)
            b = randrange(0, 100)
            radius = randint(self.width // 2, self.width)
            pygame.draw.circle(surface, (r, g, b), (x, y), radius)


class TacticalBattle:
    def __init__(self, location, attacker_faction, defender_faction, attacker_ships, defender_ships):
        self.attacker_faction = attacker_faction
        self.defender_faction = defender_faction
        self.attacker_ships = attacker_ships
        self.defender_ships = defender_ships
        self.retreat = False
        self.round = 0
        self.rounds = []
        self.starfield = generate_starfield()
        self.damage_due_attackers = 0
        self.damage_due_defenders = 0
        self.attacker_sprites = []
        self.defender_sprites = []
        self.winner = None
        self.location = location

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
