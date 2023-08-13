from constants import *
from faction_type import FactionType, faction_type_to_color
from random import shuffle, randrange, randint, choice
from fleet import Fleet
from utility import d100, coin_flip

class CenterOfGravity:
    def __init__(self, loc, turns, game):
        self.loc = loc
        self.turns = turns
        self.nodes = [i for i in filter(lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY, game.star_map.locations)]

class Faction: 
    def __init__(self, faction_type, game, personality):
        self.game = game
        self.faction_type = faction_type
        self.color = faction_type_to_color(faction_type)
        if faction_type == FactionType.PLAYER:
            self.homeworld = game.star_map.player_hw
        elif faction_type != FactionType.EXOGALACTIC_INVASION:
            self.homeworld = [i for i in filter(lambda x: x.faction_type == faction_type, game.star_map.faction_homeworlds)][0]
        self.name = game.star_map.faction_names[faction_type]
        self.personality = personality
        self.centers_of_gravity = []

    def pp(self):
        print("AI Faction Pretty-Print")
        print("\tfaction_type: {}".format(self.faction_type))
        print("\tcolor: {}".format(self.color))
        print("\tname: {}".format(self.name))
        print("\tpersonality: {}".format(self.personality.name))

    # Gets the shortest path from start_loc to end_loc which doesn't run through a 
    # system controlled by another faction.
    def shortest_uncontested_path(self, start_loc, end_loc):  

        def get_traceback(seen): 
            current = seen[-1]  
            traceback = [current["loc"]]
            seen.reverse()
            while current["loc"] is not start_loc:
                for node in seen:
                    if node["loc"] is current["via"]:
                        if node["loc"] is not start_loc:
                            traceback.append(node["loc"])
                        current = node
            traceback.reverse()
            return traceback 

        seen = [{"loc": start_loc, "via": None}]
        while True:  
            hits = False
            for node in seen:
                for loc in self.game.star_map.locations:
                    in_range = loc.ly_to(node["loc"].pos) <= DEFAULT_FUEL_RANGE_LY
                    is_child_node = node["loc"] is not loc
                    owned = loc.faction_type == self.faction_type
                    not_seen = loc not in [i for i in map(lambda x: x["loc"], seen)]
                    if in_range and is_child_node and owned and not_seen:
                        new_node = {"loc": loc, "via": node["loc"]}
                        seen.append(new_node)
                        hits = True
                        if loc is end_loc:
                            return get_traceback(seen)
            if not hits:
                break
        return None
 
    def run_behavior(self):
        # This function handles all of the logic and action of AI Empire factions,
        # on a turn-by-turn basis.
        game = self.game
        if self.faction_type == FactionType.PLAYER and not game.watch_mode:
            return
        star_map = game.star_map

        launched_attacks = 0
        activated_reserves = 0
        activated_direct_reserves = 0

        def will_attack():
            return d100()[0] <= self.personality.base_attack_chance

        def min_to_attack(needed_reserves, source, target):
            return source.ships - needed_reserves >= target.ships * self.personality.min_attack_ratio
            
        def is_hostile_neighbor_of(friendly_loc, other_loc):
            pirates = other_loc.faction_type == FactionType.PIRATES
            non_ftl = other_loc.faction_type == FactionType.NON_SPACEFARING
            own = other_loc.faction_type == self.faction_type
            in_range = friendly_loc.ly_to(other_loc.pos) <= DEFAULT_FUEL_RANGE_LY
            hostile = pirates or (not non_ftl and not own)
            return hostile and in_range

        def all_hostile_neighbors_of(loc):
            return [i for i in filter(lambda x: is_hostile_neighbor_of(loc, x), star_map.locations)]

        def all_friendly_neighbors_of(loc):
            return [i for i in filter(lambda x: x.faction_type == self.faction_type and x.pos != loc.pos and x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY, star_map.locations)]

        def nearest_friendly_system_to(loc): 
            friendly_neighbors = all_friendly_neighbors_of(loc)
            closest = None
            for system in friendly_neighbors:
                if closest is None:
                    closest = system
                else:
                    if system.get_eta_to(loc.pos) < system.get_eta_to(closest.pos):
                        closest = system
            return closest

        def all_neighbors_of(loc):
            return [i for i in filter(lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY and loc.pos != x.pos, star_map.locations)]

        owned_systems = [i for i in filter(lambda x: x.faction_type == self.faction_type, star_map.locations)]
        owned_fleets = [i for i in filter(lambda x: x.faction_type == self.faction_type, star_map.deployed_fleets)]

        # Check all routed fleets and cancel threatened waypoints:
        for fleet in owned_fleets:
            if fleet.ai_threat_check_flag:
                for waypoint in fleet.waypoints:
                    if waypoint.faction_type != self.faction_type and waypoint is not fleet.destination:
                        fleet.remove_waypoint(waypoint)

        def is_aware_of(pos):
            # can be seen by any fleet or location owned by the faction
            for owned_loc in owned_systems:
                if owned_loc.ly_to(pos) <= owned_loc.sensor_range:
                    return True
            for owned_fleet in owned_fleets:
                if owned_fleet.ly_to(pos) <= owned_fleet.sensor_range:
                    return True
            return False

        hostile_fleets = [i for i in filter(lambda x: x.faction_type != self.faction_type, star_map.deployed_fleets)]
        potential_targets = []
        for loc in star_map.locations:
            if loc.faction_type != self.faction_type:
                if is_aware_of(loc.pos) and loc not in potential_targets: 
                    potential_targets.append(loc)

        total_self_ship_count = sum(map(lambda x: x.ships, owned_systems))
        total_self_ship_count += sum(map(lambda x: x.ships, owned_fleets))
        total_hostile_ship_count = sum(map(lambda x: x.ships, filter(lambda y: y.faction_type != FactionType.PIRATES and y.faction_type != FactionType.NON_SPACEFARING, potential_targets)))
        total_hostile_ship_count += sum(map(lambda x: x.ships, hostile_fleets))

        def all_owned_fleets_in_range_of(loc):
            return [i for i in filter(lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY, owned_fleets)]

        def all_hostile_fleets_in_range_of(loc):
            return [i for i in filter(lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY, hostile_fleets)]

        def get_num_defenders(loc):
            num_defenders = loc.ships
            for fleet in all_hostile_fleets_in_range_of(loc):
                if fleet.destination == loc and is_aware_of(fleet.pos):
                    num_defenders += fleet.ships
            return num_defenders

        def get_already_inbound_attackers(loc):
            num_attackers = 0
            for fleet in all_owned_fleets_in_range_of(loc):
                if fleet.destination == loc:
                    num_attackers += fleet.ships
            return num_attackers

        def get_sources_of_attack(target):
            return [i for i in filter(lambda x: not is_threatened(x) and not x.rallying, all_friendly_neighbors_of(target))]

        def is_threatened(loc): 
            # there are incoming fleets of a threatening size
            for fleet in all_hostile_fleets_in_range_of(loc):
                if fleet.destination == loc and fleet.ships > loc.ships / 2 and is_aware_of(fleet.pos):
                    # TODO: Maybe make this part -------------^^^^^^^^^^^^^ a personality variable as well.
                    return True
            return False

        def calculate_needed_reserves(loc):
            # count hostile forces in the area
            hostile_neighbors = all_hostile_neighbors_of(loc)
            area_hostile_ship_count = 0
            strongest_threat_ship_count = 0
            for neighbor in hostile_neighbors:
                if is_aware_of(neighbor.pos) and neighbor.faction_type != FactionType.NON_SPACEFARING:
                    threat_count = neighbor.ships - 1
                    nearby_hostile_fleets = all_hostile_fleets_in_range_of(neighbor)
                    for fleet in nearby_hostile_fleets:
                        if is_aware_of(fleet.pos) and fleet.destination == neighbor:
                            threat_count += fleet.ships
                    area_hostile_ship_count += threat_count
                    if threat_count > strongest_threat_ship_count:
                        strongest_threat_ship_count = threat_count
            # count friendly forces in the area
            friendly_neighbors = [i for i in filter(lambda x: not is_threatened(x), all_friendly_neighbors_of(loc))]
            local_defender_count = 0 
            for neighbor in friendly_neighbors:  
                local_defender_count += neighbor.ships
                nearby_friendly_fleets = all_owned_fleets_in_range_of(neighbor)
                for fleet in nearby_friendly_fleets:
                    if fleet.destination == neighbor:
                        local_defender_count += fleet.ships
            # needed reserves is a portion of the hostile count minus a portion of the friendly count
            hostile_count = strongest_threat_ship_count + area_hostile_ship_count
            adjusted_hostile_count = int(hostile_count * self.personality.base_hostile_count_factor)
            adjusted_friendly_count = int(local_defender_count * self.personality.base_friendly_count_factor)
            return max(adjusted_hostile_count - adjusted_friendly_count, 1)

        def rally_check():  
            rally_points = [i for i in filter(lambda x: x.rallying, owned_systems)]
            for system in rally_points:
                needed_reserves = calculate_needed_reserves(system)
                fleets_in_range = all_owned_fleets_in_range_of(system)
                still_rallying = False
                for fleet in fleets_in_range:
                    if fleet.destination == system:
                        still_rallying = True
                if not still_rallying:
                    reasonable_attack = True
                    if is_threatened(system):
                        reasonable_attack = False
                    if system.ships - system.rally_amount < needed_reserves:
                        reasonable_attack = False
                    if reasonable_attack:
                        star_map.deploy_fleet(system, system.rally_target, system.rally_amount)
                    system.rallying = False
                    system.rally_target = None
                    system.rally_amount = 0

        rally_check()

        def is_defensible(loc):
            # Can bring reenforcements to bear before overwhelming force arrives
            num_attackers = 0
            soonest_arrival = None
            for fleet in all_hostile_fleets_in_range_of(loc):
                if fleet.destination == loc and is_aware_of(fleet.pos):
                    num_attackers += fleet.ships
                    if soonest_arrival is None:
                        soonest_arrival = fleet.get_eta()
                    elif fleet.get_eta() < soonest_arrival:
                        soonest_arrival = fleet.get_eta()

            num_defenders = loc.ships
            for fleet in all_owned_fleets_in_range_of(loc):
                if fleet.destination == loc and fleet.get_eta() < soonest_arrival:
                    num_defenders += fleet.ships

            for owned_loc in all_friendly_neighbors_of(loc):
                # Systems under threat will remain defensive instead of contributing reenforcements
                if owned_loc.get_eta_to(loc.pos) < soonest_arrival and not is_threatened(owned_loc):
                    num_defenders += owned_loc.ships - 1

            if num_attackers < num_defenders * self.personality.base_defensibility_threshold:
                return True
            return False

        def reenforce(loc):
            # send reenforcements from one or more nearby worlds to bring it up to strength against an incoming threat
            num_attackers = 0
            soonest_arrival = None
            for fleet in all_hostile_fleets_in_range_of(loc):
                if fleet.destination == loc and is_aware_of(fleet.pos):
                    num_attackers += fleet.ships
                    if soonest_arrival is None:
                        soonest_arrival = fleet.get_eta()
                    elif fleet.get_eta() < soonest_arrival:
                        soonest_arrival = fleet.get_eta()

            sources = [i for i in filter(lambda x: x.get_eta_to(loc.pos) < soonest_arrival and not is_threatened(x), all_friendly_neighbors_of(loc))]
            sending = {}
            total_en_route = 0
            for source in sources:
                sending[source] = 0
            while True:  
                if len(sources) == 0:
                    break
                if total_en_route + loc.ships >= num_attackers:
                    break
                tapped = 0
                for source in sources:
                    if source.ships > 1:
                        sending[source] += 1
                        total_en_route += 1
                    else:
                        tapped += 1
                if tapped == len(sources):
                    break

            for source in sources:
                if sending[source] > 0 and not source.rallying:
                    star_map.deploy_fleet(source, loc, sending[source])

        def is_rear_system(loc):
            # is surrounded only by friendly systems or non-FTL systems
            neighbors = all_neighbors_of(loc)
            for neighbor in neighbors:
                if neighbor.faction_type != self.faction_type:
                    return False
            return True

        def is_viable_target(loc): 
            # is within fuel range of enough ships split between close worlds that a combined attack
            # would be potentially successful
            num_defenders = get_num_defenders(loc)
            num_attackers = get_already_inbound_attackers(loc)

            if num_attackers >= num_defenders:
                # Avoid attacking systems already under attack from a previous decision
                return False

            sources = get_sources_of_attack(loc)
            for source in sources:
                reserve = calculate_needed_reserves(source)
                num_attackers += max(source.ships - reserve, 0) 

            if num_attackers >= num_defenders * self.personality.min_attack_ratio:
                return True
            return False

        def attack(loc): 
            num_defenders = get_num_defenders(loc)

            sources = get_sources_of_attack(loc)
            sending = {}
            for source in sources:
                sending[source] = 0
            max_available = 0
            for source in sources:
                needed_reserves = calculate_needed_reserves(source)
                max_available += max(source.ships - needed_reserves, 0)
            min_to_send = max(int(loc.ships * self.personality.min_attack_ratio), 0)
            max_to_send = min(max(int(loc.ships * self.personality.max_attack_ratio), min_to_send), max_available)
            
            num_to_deploy = max_to_send 
            if min_to_send < max_to_send: 
                num_to_deploy = randint(min_to_send, max_to_send)

            en_route = 0
            for source in sources:
                needed_reserves = calculate_needed_reserves(source)
                deploying = max(source.ships - needed_reserves, 0)
                en_route = min(en_route + deploying, num_to_deploy)
                sending[source] = deploying
                if en_route >= num_to_deploy:
                    break

            coordinated_attack = len(sources) > 1
            single_point_attack = len(sources) == 1
            if coordinated_attack:
                valid_rally_points = [i for i in filter(lambda x: not x.rallying, all_friendly_neighbors_of(loc))]
                if len(valid_rally_points) > 0:
                    rally_point = choice(valid_rally_points)
                    rally_point.rallying = True
                    rally_point.rally_target = loc
                    rally_point.rally_amount = en_route
                    for source in sources: 
                        star_map.deploy_fleet(source, rally_point, sending[source])
            elif single_point_attack:
                source = sources[0]
                star_map.deploy_fleet(source, loc, sending[source])

        def evacuate(loc):
            # flee to a friendly world, or to a hostile world, or not at all, depending on factors
            if loc.ships > 1:
                friendly_neighbors = all_friendly_neighbors_of(loc)
                shuffle(friendly_neighbors)
                evacuated = False

                def supporting_evac_routine(evacuated):
                    for neighbor in friendly_neighbors:
                        if is_threatened(neighbor):
                            star_map.deploy_fleet(loc, neighbor, loc.ships - 1)
                            return True
                    return False

                def friendly_evac_routine(evacuated): 
                    if not evacuated and len(friendly_neighbors) > 0:
                        target = choice(friendly_neighbors)
                        star_map.deploy_fleet(loc, target, loc.ships - 1)
                        return True
                    return False

                def hostile_evac_routine(evacuated):
                    if not evacuated:
                        neighbors = all_hostile_neighbors_of(loc)
                        weakest = None

                        def is_first_viable_target(neighbor):
                            return weakest is None and neighbor.ships < loc.ships
       
                        def is_other_viable_target(neighbor): 
                            return weakest is not None and weakest.ships < neighbor.ships and neighbor.ships < loc.ships

                        def viable_target_found():
                            return weakest is not None and loc.ships > weakest.ships * self.personality.min_attack_ratio

                        for neighbor in neighbors:
                            if is_first_viable_target(neighbor):
                                weakest = neighbor
                            elif is_other_viable_target(neighbor):
                                weakest = neighbor
                        if viable_target_found():
                            star_map.deploy_fleet(loc, weakest, loc.ships - 1)

                evacuated = supporting_evac_routine(evacuated)
                if not evacuated:
                    evacuated = friendly_evac_routine(evacuated)
                if not evacuated:
                    hostile_evac_routine(evacuated)

        threatened_systems = [i for i in filter(lambda x: is_threatened(x), owned_systems)]
        shuffle(threatened_systems)

        understrength_systems = [i for i in filter(lambda x: x.ships < calculate_needed_reserves(x), owned_systems)]
        shuffle(understrength_systems)

        def handle_centers_of_gravity():
            if len(self.centers_of_gravity) < self.personality.centers_of_gravity:
                if len(understrength_systems) + len(threatened_systems) == 0:
                    return
                center_of_gravity = CenterOfGravity(choice(understrength_systems + threatened_systems), self.personality.turns_to_pull, self.game)
                self.centers_of_gravity.append(center_of_gravity)

            for cog in self.centers_of_gravity:
                cog.turns -= 1
                if is_rear_system(cog.loc):
                    cog.turns = 0
            self.centers_of_gravity = [i for i in filter(lambda x: x.turns > 0, self.centers_of_gravity)]

        def activate_reserves(loc): 
            nonlocal activated_reserves
            nonlocal activated_direct_reserves
            # Route reserves either directly to the front, indirectly towards the front,
            # or simply to buzz around nearby systems collecting ships. 
            def route(dest_list):
                nonlocal activated_reserves
                nonlocal activated_direct_reserves
                under_max_reserves = activated_reserves < self.personality.max_activated_reserves
                under_max_direct_reserves = activated_direct_reserves < self.personality.max_activated_direct_reserves
                if under_max_reserves and under_max_direct_reserves:
                    path = self.shortest_uncontested_path(loc, choice(dest_list))
                    if path is not None:
                        target = path[0]
                        # Some personality types directly route a higher level of their reenforcements to a front
                        if d100()[0] <= self.personality.base_direct_to_front_chance_out_of_100:
                            star_map.deploy_fleet(loc, target, loc.ships - 1, True, path)
                        # While others simply make a short hop towards one, providing a more flexible but slower
                        # activation of their reserves.
                        else:
                            star_map.deploy_fleet(loc, target, loc.ships - 1)
                        activated_reserves += 1
                        activated_direct_reserves += 1
                        return True
                return False

            routed = False
            # Above this threshold, they'll route reserves directly to the front
            # towards threatened or understrength systems, or centers of gravity when applicable
            if loc.ships > self.personality.base_reserve_threshold: 
                if len(self.centers_of_gravity) > 0 and d100()[0] <= self.personality.center_of_gravity_chance_out_of_100:
                    cog = choice(self.centers_of_gravity)
                    routed = route(cog.nodes)
                elif len(threatened_systems + understrength_systems) > 0:
                    routed = route(understrength_systems + threatened_systems)
            # Or, they'll pool reserves among nearby planets. A lower base_reserve_threshold
            # creates faster pooling, but less defensive depth in case of a breakthrough
            if not routed and loc.ships > self.personality.base_reserve_pool_threshold: 
                friendly_fleets = all_owned_fleets_in_range_of(loc)
                incoming = False
                for fleet in friendly_fleets:
                    if fleet.destination is loc:
                        incoming = True
                        break
                if not incoming and activated_reserves < self.personality.max_activated_reserves:
                    friendly_neighbors = all_friendly_neighbors_of(loc)
                    target = choice(friendly_neighbors)
                    star_map.deploy_fleet(loc, target, loc.ships - 1)
                    activated_reserves += 1

        # Handle player reenforcements in watch_mode
        if self.faction_type == FactionType.PLAYER and game.watch_mode:
            # Player in Watch mode will bank some reenforcements to prioritize
            # threatened worlds later. Not as well as a good human player though.
            banking = coin_flip() and len(threatened_systems) == 0 and len(understrength_systems) == 0
            if not banking:
                while game.player_reenforcement_pool > 0:
                    for loc in threatened_systems:
                        if game.player_reenforcement_pool > 0:
                            loc.ships += 1
                            game.player_reenforcement_pool -= 1
                    for loc in understrength_systems:
                        if game.player_reenforcement_pool > 0:
                            loc.ships += 1
                            game.player_reenforcement_pool -= 1
                    if game.player_reenforcement_pool > 0:
                        loc = choice(owned_systems)
                        loc.ships += 1
                        game.player_reenforcement_pool -= 1

        rear_systems = [i for i in filter(lambda x: is_rear_system(x), owned_systems)]
        shuffle(rear_systems)

        defensible_systems = []
        evac_list = []
        for threatened_system in threatened_systems:
            if is_defensible(threatened_system):
                defensible_systems.append(threatened_system)
            else:
                evac_list.append(threatened_system)

        shuffle(defensible_systems)
        shuffle(evac_list)

        viable_target_list = [i for i in filter(lambda x: is_viable_target(x), potential_targets)]
        shuffle(viable_target_list)

        handle_centers_of_gravity() 

        for threatened_loc in defensible_systems:
            if is_defensible(threatened_loc):  # this can change throughout the loop
                reenforce(threatened_loc)
        for threatened_loc in evac_list:
            if not is_defensible(threatened_loc):
                evacuate(threatened_loc)
        for viable_target in viable_target_list:
            if is_viable_target(viable_target) and will_attack(): # is_viable_target() can change throughout the loop
                attack(viable_target)
        for rear_system in rear_systems:
            activate_reserves(rear_system)

