from clickable import Clickable
from constants import *
from pygame.math import Vector2
from math import ceil


class Fleet(Clickable):
    def __init__(self, name, pos, faction_type, ships, destination, speed=DEFAULT_SPEED_LY):
        hit_box =  (pos[0] - FLEET_HITBOX_SIDE_PX / 2, pos[1] - FLEET_HITBOX_SIDE_PX / 2, FLEET_HITBOX_SIDE_PX, FLEET_HITBOX_SIDE_PX)
        super().__init__(hit_box)
        self.pos = pos
        self.name = name
        self.faction_type = faction_type
        self.ships = ships
        self.destination = destination
        self.speed = speed
        self.in_sensor_view = False
        self.sensor_range = DEFAULT_FLEET_SENSOR_RANGE_LY

    # Moves the fleet LY * speed towards its destination
    def move(self):
        new_pos = Vector2(self.pos).move_towards(Vector2(self.destination.pos),
                                                 self.speed * LY)
        hit_box =  (new_pos[0] - FLEET_HITBOX_SIDE_PX / 2, new_pos[1] - FLEET_HITBOX_SIDE_PX / 2, FLEET_HITBOX_SIDE_PX, FLEET_HITBOX_SIDE_PX)
        self.pos = new_pos
        self.rect = hit_box

    # Takes point on the map and returns the # of LYs between them
    def ly_to(self, point):
        return Vector2(self.pos).distance_to(Vector2(point)) / LY

    # Returns the # of turns until destination reached by 
    # dividing the distance in LY to target by speed 
    # (which is LY/turn)
    def get_eta(self):
        return ceil(self.ly_to(self.destination.pos) / self.speed)

    # Simply piggy-backs off of the dimensions for clicking. For now,
    # fleets can't engage each other in interstellar space -- only at
    # star systems. For now.
    def in_range(self, pos):
        return self.clicked(pos)
