from constants import *
from faction_type import FactionType, faction_type_to_color
from random import shuffle, randrange, randint, choice
from fleet import Fleet
from utility import d100, coin_flip

class StrategicObjective:
    def __init__(self, faction_type):
        self.faction_type = faction_type

class Faction:
    def __init__(self, faction_type, star_map):
        self.faction_type = faction_type
        self.color = faction_type_to_color(faction_type)
        if faction_type == FactionType.PLAYER:
            self.homeworld = star_map.player_hw
        else:
            self.homeworld = [i for i in filter(lambda x: x.faction_type == faction_type, star_map.faction_homeworlds)][0]
        self.name = star_map.faction_names[faction_type]
        self.personality_traits = []  # un-implemented
        self.strategic_objectives = []  # un-implemented

    def run_behavior(self, game):
        # This function handles all of the logic and action of AI Empire factions,
        # on a turn-by-turn basis.
        # TODO: Diplomacy logic
        # TODO: Longer Strategic Objectives 
        # TODO: Personality traits
        star_map = game.star_map

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
        hostile_fleets = [i for i in filter(lambda x: x.faction_type != self.faction_type, star_map.deployed_fleets)]

        def all_owned_fleets_in_range_of(loc):
            return [i for i in filter(lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY, owned_fleets)]

        def all_hostile_fleets_in_range_of(loc):
            return [i for i in filter(lambda x: x.ly_to(loc.pos) <= DEFAULT_FUEL_RANGE_LY, hostile_fleets)]

        def is_aware_of(pos):
            # can be seen by any fleet or location owned by the faction
            for owned_loc in owned_systems:
                if owned_loc.ly_to(pos) <= owned_loc.sensor_range:
                    return True
            for owned_fleet in owned_fleets:
                if owned_fleet.ly_to(pos) <= owned_fleet.sensor_range:
                    return True
            return False

        def is_threatened(loc):
            # there are incoming fleets
            for fleet in all_hostile_fleets_in_range_of(loc):
                if fleet.destination == loc and is_aware_of(fleet.pos):
                    return True
            return False
            # TODO: Maybe also a function for border worlds that just happen to be close to strong enemy systems.
            #       That would be useful for having the AI create "front lines" and manage reserves better, in
            #       future versions.

        def rally_check():
            for system in owned_systems:
                if system.faction_type == self.faction_type and not is_threatened(system) and system.rallying:
                    fleets_in_range = all_owned_fleets_in_range_of(system)
                    still_rallying = False
                    for fleet in fleets_in_range:
                        if fleet.destination == system:
                            still_rallying = True
                    if not still_rallying and system.ships > 1:
                        # TODO: Maybe leave some reserves and/or check to make sure system hasn't
                        #       been heavily reenforced in the meantime.
                        if system.ships - 1 >= system.rally_target.ships:
                            # Last-minute re-evaluation to make sure it's still a good attack
                            star_map.deploy_fleet(system, system.rally_target, system.ships - 1)
                        system.rallying = False
                        system.rally_target = None
                    

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

            if num_attackers < num_defenders * AI_EMPIRE_EVACUATION_THRESHOLD:
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
            num_defenders = loc.ships
            for fleet in all_hostile_fleets_in_range_of(loc):
                if fleet.destination == loc and is_aware_of(fleet.pos):
                    num_defenders += fleet.ships

            num_attackers = 0
            for fleet in all_owned_fleets_in_range_of(loc):
                if fleet.destination == loc:
                    num_attackers += fleet.ships

            if num_attackers >= num_defenders:
                # Avoid attacking systems already under attack from a previous decision
                return False

            sources = [i for i in filter(lambda x: not is_threatened(x) and not x.rallying, all_friendly_neighbors_of(loc))]
            for source in sources:
                num_attackers += source.ships - 1

            if num_attackers >= num_defenders * AI_EMPIRE_OVERMATCH_THRESHOLD:
                return True
            return False

        def attack(loc): 
            num_defenders = loc.ships
            for fleet in all_hostile_fleets_in_range_of(loc):
                if fleet.destination == loc and is_aware_of(fleet.pos):
                    num_defenders += fleet.ships

            sources = [i for i in filter(lambda x: not is_threatened(x) and not x.rallying, all_friendly_neighbors_of(loc))]
            en_route = [i for i in filter(lambda x: x.destination == loc, all_owned_fleets_in_range_of(loc))]
            num_en_route = sum([i for i in map(lambda x: x.ships, en_route)])
            sending = {}
            for source in sources:
                sending[source] = 0
            max_available = 0
            for source in sources:
                max_available += source.ships - 1
            min_to_send = int((loc.ships - num_en_route) * AI_EMPIRE_MIN_ATTACK_RATIO)
            if min_to_send < 0:
                min_to_send = 0
            max_to_send = int((loc.ships - num_en_route) * AI_EMPIRE_MAX_ATTACK_RATIO)
            if max_to_send < min_to_send:
                max_to_send = min_to_send
            if max_to_send > max_available:
                max_to_send = max_available
            num_to_deploy = randint(min_to_send, max_to_send)
            en_route = 0
            for source in sources:
                if en_route >= num_to_deploy:
                    break
                deploying = source.ships - 1
                if en_route + deploying >= max_to_send:
                    deploying = max_to_send - en_route
                en_route += deploying
                sending[source] = deploying

            coordinated_attack = len(sources) > 1
            if coordinated_attack:
                rally_point = nearest_friendly_system_to(loc)
                rally_point.rallying = True
                rally_point.rally_target = loc
                for source in sources: # TODO: Rally these
                    if sending[source] > 0:
                        star_map.deploy_fleet(source, rally_point, sending[source])
            elif len(sources) > 0:
                star_map.deploy_fleet(sources[0], loc, sending[sources[0]])

        def evacuate(loc):
            # flee to a friendly world, or to a hostile world, or not at all, depending on factors
            # Prioritize friendly threatened worlds, then any friendly world, and finally, if no other option,
            # the weakest neighboring world which doesn't pass the threshold for evac.
            # If none of those are viable at all, it will stay put and hope for good dice rolls
            # TODO: This can be improved. Hostile evacs are lacking.
            if loc.ships > 1:
                friendly_neighbors = all_friendly_neighbors_of(loc)
                shuffle(friendly_neighbors)
                evacuated = False
                for neighbor in friendly_neighbors:
                    if is_threatened(neighbor):
                        star_map.deploy_fleet(loc, neighbor, loc.ships - 1)
                        evacuated = True
                        break
                if not evacuated and len(friendly_neighbors) > 0:
                    target = choice(friendly_neighbors)
                    evacuated = True
                    star_map.deploy_fleet(loc, target, loc.ships - 1)
                if not evacuated:
                    neighbors = all_hostile_neighbors_of(loc)
                    weakest = None
                    for neighbor in neighbors:
                        if weakest is None:
                            weakest = neighbor
                        elif weakest.ships < neighbor.ships:
                            weakest = neighbor
                    if loc.ships < weakest.ships * AI_EMPIRE_EVACUATION_THRESHOLD:
                        star_map.deploy_fleet(loc, weakest, loc.ships - 1)

        def activate_reserves(loc):
            # move to a nearby friendly world
            if loc.ships > 10:
                friendly_neighbors = all_friendly_neighbors_of(loc)
                target = choice(friendly_neighbors)
                star_map.deploy_fleet(loc, target, loc.ships - 1)

        threatened_systems = [i for i in filter(lambda x: is_threatened(x), owned_systems)]
        shuffle(threatened_systems)

        # Handle player reenforcements in watch_mode
        if self.faction_type == FactionType.PLAYER and game.watch_mode:
            # Player in Watch mode will bank some reenforcements to prioritize
            # threatened worlds later. Not as well as a good human player though.
            banking = coin_flip() and len(threatened_systems) == 0
            if not banking:
                while game.player_reenforcement_pool > 0:
                    for loc in threatened_systems:
                        if game.player_reenforcement_pool > 0:
                            loc.ships += 1
                            game.player_reenforcement_pool -= 1
                    if game.player_reenforcement_pool > 0:
                        loc = choice(owned_systems)
                        loc.ships += 1
                        game.player_reenforcement_pool -= 1

        potential_targets = []
        for loc in star_map.locations:
            if loc.faction_type != self.faction_type:
                if is_aware_of(loc.pos) and loc not in potential_targets:
                    potential_targets.append(loc)

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

        for threatened_loc in defensible_systems:
            if is_defensible(threatened_loc):  # this can change throughout the loop
                reenforce(threatened_loc)
        for threatened_loc in evac_list:
            evacuate(threatened_loc)
        for viable_target in viable_target_list:
            if is_viable_target(viable_target):  # this can change throughout the loop
                if d100()[0] <= BASE_AI_EMPIRE_ATTACK_CHANCE_OUT_OF_100:
                    attack(viable_target)
        for rear_system in rear_systems:
            activate_reserves(rear_system)

