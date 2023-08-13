from clickable import Clickable
from constants import *
from pygame.math import Vector2
from math import ceil, floor

class Fleet(Clickable):
    def __init__(self, name, pos, faction_type, ships, destination, veterancy):
        hit_box =  (pos[0] - FLEET_HITBOX_SIDE_PX / 2, pos[1] - FLEET_HITBOX_SIDE_PX / 2, FLEET_HITBOX_SIDE_PX, FLEET_HITBOX_SIDE_PX)
        super().__init__(hit_box)
        self.pos = pos
        self.name = name
        self.faction_type = faction_type
        self.ships = ships
        self.destination = destination 
        self.in_sensor_view = False
        self.sensor_range = DEFAULT_FLEET_SENSOR_RANGE_LY
        self.to_be_removed = False
        self.veterancy_out_of_100 = veterancy
        self.speed = DEFAULT_SPEED_LY
        self.waypoints = [] 
        self.ai_threat_check_flag = False

    def add_waypoint(self, loc): 
        self.waypoints.append(loc)  

    def remove_waypoint(self, loc):
        if loc in self.waypoints:
            if loc == self.waypoints[0]:
                return
            new_waypoint_list = [i for i in self.waypoints]
            new_waypoint_list.remove(loc)
            final_waypoint_list = []
            current = self.pos
            for waypoint in new_waypoint_list:
                in_range = Vector2(waypoint.pos).distance_to(current) <= DEFAULT_FUEL_RANGE_LY * LY
                if not in_range:
                    break
                final_waypoint_list.append(waypoint)
                current = waypoint.pos
            self.waypoints = final_waypoint_list

    def get_num_vets(self):   
        return floor((self.veterancy_out_of_100 / 100) * self.ships) 

    def get_percent_vets(self):
        return floor((self.get_num_vets() / self.ships) * 100)

    def get_veterancy_roll_bonus(self):
        bonus = self.veterancy_out_of_100
        if bonus >= VETERANCY_ROLL_BONUS_THRESHOLD_2:
            return VETERANCY_ROLL_BONUS_2
        elif bonus >= VETERANCY_ROLL_BONUS_THRESHOLD_1:
            return VETERANCY_ROLL_BONUS_1
        else: 
            return 0

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

    def arrived(self):
        # testing: this likely needs a margin of error? This should be fool-proof...
        return self.get_eta() < 1

