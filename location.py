from constants import *
from enum import Enum
from clickable import Clickable
from random import randint, randrange, choice
from utility import d100, d20
from pygame.math import Vector2
from faction_type import FactionType, ai_empire_faction_types
from math import ceil
import pygame
from pygame.math import Vector2

class LocationType(Enum):
    STAR_SYSTEM = 1

def generate_starfield():
    local_star_colors = ["red", "purple", "yellow", "orange"]
    starfield_surface = pygame.Surface((SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX))
    # Background stars
    num_stars = int((SCREEN_WIDTH_PX * SCREEN_HEIGHT_PX) * STARFIELD_DENSITY)
    for _ in range(num_stars):
        pos = (randrange(0, SCREEN_WIDTH_PX), randrange(0, SCREEN_HEIGHT_PX))
        radius = 1
        if d20()[0] <= 1:
            radius = 2
        pygame.draw.circle(starfield_surface, "white", pos, radius)
    # Up to 2 local stars
    num_local_stars = randint(1, 2)
    for star in range(num_local_stars):
        star_pos = (randrange(0, SCREEN_WIDTH_PX), randrange(0, SCREEN_HEIGHT_PX))
        star_radius = randint(LOCAL_STAR_MIN_SIZE, LOCAL_STAR_MAX_SIZE)
        pygame.draw.circle(starfield_surface, choice(local_star_colors), star_pos, star_radius)
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
        pygame.draw.polygon(starfield_surface, (0, continent_color, 0), points)
    # Cloud cover
    num_cloud_px = int(planet_px_rect[2] * planet_px_rect[3] * LOCAL_CLOUD_DENSITY)
    for _ in range(num_cloud_px):
        radius = 5  # for now
        x = randrange(planet_px_rect[0], planet_px_rect[0] + planet_px_rect[2] - radius)
        y = randrange(planet_px_rect[1], planet_px_rect[1] + planet_px_rect[3] - radius)
        in_circle = Vector2((x, y)).distance_to(planet_pos) <= planet_radius
        cloud_color = randrange(COLOR_CLOUDS_MIN, COLOR_CLOUDS_MAX)
        if in_circle:
            pygame.draw.circle(starfield_surface, (cloud_color, cloud_color, cloud_color), (x, y), radius)

    return starfield_surface

class Location(Clickable):
    def __init__(self, name, pos, location_type, faction_type=None, ships=0):
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
        self.starfield = generate_starfield()
        self.rallying = False
        self.rally_target = None

    def under_threat(self, fleets):
        for fleet in fleets:
            in_range = self.ly_to(fleet.pos) <= DEFAULT_FUEL_RANGE_LY
            pirates = fleet.faction_type == FactionType.PIRATES
            not_own_faction = fleet.faction_type != self.faction_type
            if in_range and (pirates or not_own_faction):
                return True
        return False

    def will_spawn_reenforcements(self, hard_mode):
        if self.faction_type == FactionType.NON_SPACEFARING and self.ships >= NON_SPACEFARING_PRODUCTION_LIMIT_THRESHOLD:
            # Non-FTL factions are not as capable of building up reenforcements
            return d100()[0] <= self.reenforce_chance_out_of_100 // NON_SPACEFARING_PRODUCTION_PENALTY
        elif self.faction_type in ai_empire_faction_types and hard_mode:
            return d100()[0] <= self.reenforce_chance_out_of_100 + HARD_MODE_PRODUCTION_BONUS
        else:
            return d100()[0] <= self.reenforce_chance_out_of_100

    # Takes point on the map and returns the # of LYs between them
    def ly_to(self, point):
        return Vector2(self.pos).distance_to(Vector2(point)) / LY

    def get_eta_to(self, pos):
        return ceil(self.ly_to(pos) / DEFAULT_SPEED_LY)

