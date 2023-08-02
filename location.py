from constants import *
from enum import Enum
from clickable import Clickable
from random import randint, randrange, choice
from utility import d100, d20, coin_flip
from pygame.math import Vector2
from faction_type import FactionType, ai_empire_faction_types
from math import ceil
import pygame
from pygame.math import Vector2

class LocationType(Enum):
    STAR_SYSTEM = 1

def mountain_color():
    val = randint(COLOR_MOUNTAINS_MIN, COLOR_MOUNTAINS_MAX)
    return (val, val, val)

def desert_color(): 
    r = randint(COLOR_DESERT_MIN, COLOR_DESERT_MAX)
    g = randint(COLOR_DESERT_MIN, COLOR_DESERT_MAX)
    b = max(randint(COLOR_DESERT_MIN, COLOR_DESERT_MAX) // 2, 0)
    return (r, g, b) 

def lush_color():
    g = randint(COLOR_MOUNTAINS_MIN, COLOR_MOUNTAINS_MAX)
    return (0, g, 0)

def land_color(): 
    roll = d100()[0]  # not true mutually exclusive percents, but close enough for what I'm trying to do
    if roll < SEA_CHANCE_OUT_OF_100:
        return COLOR_OCEANS
    if roll < DESERT_CHANCE_OUT_OF_100:
        return desert_color()
    elif roll < MOUNTAIN_CHANCE_OUT_OF_100: 
        return mountain_color()
    return lush_color()

def star_red(): 
    r = randint(200, 255)
    return (r, 0, 0)

def star_orange_or_yellow(): 
    r = randint(200, 255)
    g = randint(200, 255)
    return (r, g, 0)

def star_white(): 
    return (255, 255, 255)

def star_purple_or_blue(): 
    if coin_flip():
        r = randint(100, 150)
        g = randint(100, 150)
        return (r, g, 255)
    else:
        r = randint(200, 255)
        b = randint(200, 255)
        return (r, 0, b)

def random_star_color(): 
    colors = [star_red, star_orange_or_yellow]
    if d100()[0] == 1:
        return star_purple_or_blue()
    elif d100()[0] <= 10:
        return star_white()
    return choice(colors)()

def generate_starfield(): # TODO: invaded variant
    starfield_surface = pygame.Surface((SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX))
    # Background stars
    num_stars = int((SCREEN_WIDTH_PX * SCREEN_HEIGHT_PX) * STARFIELD_DENSITY)
    radius = None
    for _ in range(num_stars):
        pos = (randrange(0, SCREEN_WIDTH_PX), randrange(0, SCREEN_HEIGHT_PX))
        radius = 1
        if d20()[0] <= 1:
            radius = 2
        pygame.draw.circle(starfield_surface, "white", pos, radius)
    # Up to 3 local stars
    num_local_stars = randint(1, 2)
    for star in range(num_local_stars):
        star_pos = (randrange(0, SCREEN_WIDTH_PX), randrange(0, SCREEN_HEIGHT_PX))
        star_radius = randint(LOCAL_STAR_MIN_SIZE, LOCAL_STAR_MAX_SIZE)
        pygame.draw.circle(starfield_surface, random_star_color(), star_pos, star_radius)
    # The planet itself
    planet_pos = (randrange(0, SCREEN_WIDTH_PX), randrange(0, SCREEN_HEIGHT_PX))
    planet_radius = randint(LOCAL_PLANET_MIN_SIZE, LOCAL_PLANET_MAX_SIZE)
    pygame.draw.circle(starfield_surface, COLOR_OCEANS, planet_pos, planet_radius)
    planet_px_rect = (planet_pos[0] - planet_radius, planet_pos[1] - planet_radius, planet_radius * 2, planet_radius * 2)
    # Continents 
    num_continents = randint(NUM_CONTINENTS_MIN, NUM_CONTINENTS_MAX)
    for _ in range(num_continents):
        points = []
        num_points = randint(NUM_CONTINENT_POINTS_MIN, NUM_CONTINENT_POINTS_MAX)
        while len(points) < num_points:
            x = randrange(planet_px_rect[0], planet_px_rect[0] + planet_px_rect[2] - radius)
            y = randrange(planet_px_rect[1], planet_px_rect[1] + planet_px_rect[3] - radius)
            in_circle = Vector2((x, y)).distance_to(planet_pos) <= planet_radius
            if in_circle:
                points.append((x, y))
        continent_color = randrange(COLOR_CONTINENTS_MIN, COLOR_CONTINENTS_MAX)
        pygame.draw.polygon(starfield_surface, land_color(), points)
    # Cloud cover
    num_cloud_px = int(planet_px_rect[2] * planet_px_rect[3] * LOCAL_CLOUD_DENSITY)
    for _ in range(num_cloud_px):
        radius = CLOUD_RADIUS_PX
        x = randrange(planet_px_rect[0], planet_px_rect[0] + planet_px_rect[2] - radius)
        y = randrange(planet_px_rect[1], planet_px_rect[1] + planet_px_rect[3] - radius)
        in_circle = Vector2((x, y)).distance_to(planet_pos) <= planet_radius
        cloud_color = randrange(COLOR_CLOUDS_MIN, COLOR_CLOUDS_MAX)
        if in_circle:
            pygame.draw.circle(starfield_surface, (cloud_color, cloud_color, cloud_color), (x, y), radius)

    return (starfield_surface, planet_pos, planet_radius)

class Location(Clickable):
    def __init__(self, name, pos, location_type, grid_pos, faction_type=None, ships=0):
        hit_box =  (pos[0] - LOCATION_HITBOX_SIDE_PX / 2, pos[1] - LOCATION_HITBOX_SIDE_PX / 2, LOCATION_HITBOX_SIDE_PX, LOCATION_HITBOX_SIDE_PX)
        super().__init__(hit_box)
        self.name = name
        self.pos = pos
        self.locationType = location_type
        self.faction_type = faction_type
        self.ships = ships
        self.reenforce_chance_out_of_100 = randint(DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MIN,
                                                   DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MAX)
        self.sensor_range = randint(DEFAULT_MIN_SENSOR_RANGE_LY, DEFAULT_MAX_SENSOR_RANGE_LY)
        self.in_sensor_view = False
        self.starfield, self.planet_pos, self.planet_radius = generate_starfield()
        self.rallying = False
        self.rally_target = None
        self.rally_amount = 0
        self.battles = 0
        self.grid_pos = grid_pos

    def decimate(self):
        self.reenforce_chance_out_of_100 = POST_INVASION_REENFORCEMENT_CHANCE
        colors = [COLOR_FOG, COLOR_FOGGED_STAR, COLOR_DECIMATION_RED, COLOR_DECIMATION_PURPLE, COLOR_DECIMATION_ORANGE]
        planet_px_rect = (self.planet_pos[0] - self.planet_radius, self.planet_pos[1] - self.planet_radius, self.planet_radius * 2, self.planet_radius * 2)
        num_cloud_px = int(planet_px_rect[2] * planet_px_rect[3] * DECIMATED_CLOUD_DENSITY)
        for _ in range(num_cloud_px):
            radius = CLOUD_RADIUS_PX
            x = randrange(planet_px_rect[0], planet_px_rect[0] + planet_px_rect[2] - radius)
            y = randrange(planet_px_rect[1], planet_px_rect[1] + planet_px_rect[3] - radius)
            in_circle = Vector2((x, y)).distance_to(self.planet_pos) <= self.planet_radius
            cloud_color = choice(colors)
            if in_circle:
                pygame.draw.circle(self.starfield, cloud_color, (x, y), radius)

    def under_threat(self, fleets):
        for fleet in fleets:
            in_range = self.ly_to(fleet.pos) <= DEFAULT_FUEL_RANGE_LY
            pirates = fleet.faction_type == FactionType.PIRATES
            not_own_faction = fleet.faction_type != self.faction_type
            if in_range and (pirates or not_own_faction):
                return True
        return False

    def will_spawn_reenforcements(self, hard_mode, last_faction_buff): 
        if self.faction_type == FactionType.EXOGALACTIC_INVASION:
            # invaders don't spawn reenforcements
            return False
        if self.faction_type == FactionType.NON_SPACEFARING and self.ships >= NON_SPACEFARING_PRODUCTION_LIMIT_THRESHOLD:
            # Non-FTL factions are not as capable of building up reenforcements
            return d100()[0] <= self.reenforce_chance_out_of_100 // NON_SPACEFARING_PRODUCTION_PENALTY
        elif self.faction_type in ai_empire_faction_types and hard_mode:
            return d100()[0] <= self.reenforce_chance_out_of_100 + HARD_MODE_PRODUCTION_BONUS
        elif self.faction_type in ai_empire_faction_types and self.faction_type != FactionType.PLAYER and last_faction_buff:
            return d100()[0] <= self.reenforce_chance_out_of_100 + LAST_FACTION_BUFF_PRODUCTION_BONUS
        else:
            return d100()[0] <= self.reenforce_chance_out_of_100

    # Takes point on the map and returns the # of LYs between them
    def ly_to(self, point):
        return Vector2(self.pos).distance_to(Vector2(point)) / LY

    def get_eta_to(self, pos):
        return ceil(self.ly_to(pos) / DEFAULT_SPEED_LY)

