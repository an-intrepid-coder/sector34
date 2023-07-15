from constants import *
from enum import Enum
from clickable import Clickable
from random import randint
from utility import d100
from pygame.math import Vector2
from faction import Faction


class LocationType(Enum):
    STAR_SYSTEM = 1


class Location(Clickable):
    def __init__(self, name, pos, location_type, faction=None, ships=0):
        super().__init__((pos[0], pos[1], LOCATION_HITBOX_SIDE_PX, LOCATION_HITBOX_SIDE_PX))
        self.name = name
        self.pos = pos
        self.locationType = location_type
        self.faction = faction
        self.ships = ships
        self.reenforce_chance_out_of_100 = randint(DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MIN,
                                                   DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MAX)
        self.sensor_range = randint(DEFAULT_MIN_SENSOR_RANGE_LY, DEFAULT_MAX_SENSOR_RANGE_LY)

        self.in_sensor_view = False

    def under_threat(self, fleets):
        for fleet in fleets:
            in_range = self.ly_to(fleet.pos) <= DEFAULT_FUEL_RANGE_LY
            pirates = fleet.faction == Faction.PIRATES
            not_own_faction = fleet.faction != self.faction
            if in_range and (pirates or not_own_faction):
                return True
        return False

    def will_spawn_reenforcements(self):
        return d100()[0] < self.reenforce_chance_out_of_100

    # Takes point on the map and returns the # of LYs between them
    def ly_to(self, point):
        return Vector2(self.pos).distance_to(Vector2(point)) / LY
