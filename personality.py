class Personality: 
    def __init__(self, base_attack_chance, base_hostile_count_factor, base_friendly_count_factor, base_defensibility_threshold, min_attack_ratio, max_attack_ratio, base_reserve_threshold, base_reserve_pool_threshold, base_direct_to_front_chance_out_of_100, max_activated_reserves, max_activated_direct_reserves, centers_of_gravity, turns_to_pull, center_of_gravity_chance_out_of_100):
        # base_attack_chance is the likelyhood of launching an attack, given the opportunity
        self.base_attack_chance = base_attack_chance 
        # base_hostile_count_factor is the degree to which local hostile ships in an area are considered when
        #   making, for example, decisions about reserve-keeping.
        self.base_hostile_count_factor = base_hostile_count_factor 
        # base_friendly_count_factor is the degree to which local friendly ships in an area are considered when
        #   making, for example, decisions about reserve-keeping.
        self.base_friendly_count_factor = base_friendly_count_factor 
        # base_defensibility_threshold is a multiplier placed on a hypothetical defending fleet, and is used
        #   to determine if an area is defensible. The higher it is, the more it will expect to be able to
        #   reenforce an area to consider it "defensible".
        self.base_defensibility_threshold = base_defensibility_threshold  
        # min_attack_ratio and max_attack_ratio are used to determine the size of actual attacks when launched,
        #   as it's chosen within this range. While base_overmatch_threshold is the guesstimate used for most layers,
        #   this range is what gives individual attacks a little variance. It can affect the AI's propensity to either
        #   launch unwise attacks, or else behave in a turtle-like fashion.
        self.min_attack_ratio = min_attack_ratio  
        self.max_attack_ratio = max_attack_ratio 
        # base_reserve_threshold is the number of idle ships on a rear system which must exist before it decides to
        #   move them somewhere towards the front. If this number is very low, and max_activated_reserves is also not
        #   very low, it will negatively affect performance (because currently each directly routed fleet runs a 
        #   breadth-first-search to build its waypoint list).
        self.base_reserve_threshold = base_reserve_threshold
        # base_reserve_pool_threshold is the number at which it decides to pool reserves with nearby ones. 
        #   while base_reserve_threshold is the number at which the AI sends its "charged" shots to the front,
        #   base_reserve_pool_threshold is the number which decides how fast fleets "buzz around" their neighborhood
        #   collecting ships until they reach base_reserve_threshold to be activated. On very large scale maps,
        #   this could matter for defense in depth but the values I've used for Haymaker, Water, and SnappingTurtle
        #   all hang around a similar zone of performance.
        self.base_reserve_pool_threshold = base_reserve_pool_threshold
        # base_direct_to_front_chance_out_of_100 is the chance that reenforcements will be routed directly
        #   to a front line system instead of indirectly. This affects the level of defensive flexibility,
        #   but can lead to sharper attacks also. Like the above variables, this would probably matter more on a larger
        #   map.
        self.base_direct_to_front_chance_out_of_100 = base_direct_to_front_chance_out_of_100
        # max_activated_reserves is the max number of reserves that will be activated on a given turn. This is emergently
        #   related to the reserve thresholds and direct_to_front_chance. This would need to scale up on larger maps.
        self.max_activated_reserves = max_activated_reserves
        # max_activated_direct_reserves is the max number of reserves that will be activated with complete waypoint lists
        #   on a given turn. This is emergently related to the reserve thresholds and direct_to_front_chance. 
        #   This would need to scale up on larger maps. Of note is that in a 1v1, all other things being equal,
        #   3 seems to often beat 140 (the max that would make sense for this map size), although automated tests would
        #   be needed to confirm this. If so (and I believe it is the case that it is so) then it's because 3/turn allows
        #   the AI player to adapt more flexibly to a changing situation while the one set to 140/turn would over-commit
        #   from time to time. But that's a subtle difference at the scale of the current game. Note that the AI checks
        #   every turn if any of its waypointed reenforcements are headed for a system that's fallen under enemy control,
        #   and will cancel those waypoints (which can sometimes adapt the route, while at other times it'll cut the
        #   route short, causing them to be re-routed the next time towards somewhere else).
        self.max_activated_direct_reserves = max_activated_direct_reserves
        # centers_of_gravity are locations on the map which the AI personality type will direct its activated reserves
        #   towards, when they are not "pooling". So a type with a higher base_reserve_pool_threshold will spend more
        #   time gathering reserves before sending them, in any case.
        self.centers_of_gravity = centers_of_gravity
        # turns_to_pull is the number of turns a given center of gravity will be active. 
        self.turns_to_pull = turns_to_pull
        # center_of_gravity_chance_out_of_100 is the chance that activated reserves will go towards a center of gravity,
        #   instead of being equally distributed along "front line" areas. 
        self.center_of_gravity_chance_out_of_100 = center_of_gravity_chance_out_of_100

# SnappingTurtle "charges" its shots, and it only sends a small amount of deep reserves to the front per turn even when 
# they are fully "charged". This makes it slow on the attack, and not as quick to adapt to a changing front, but with a 
# better "cushion" and less "brittle"-ness behind the front line, than some of the other types.
class SnappingTurtle(Personality):
    def __init__(self): 
        self.name = "Snapping Turtle"
        base_attack_chance = 85
        base_hostile_count_factor = .45
        base_friendly_count_factor = .35
        base_defensibility_threshold = 2.5
        min_attack_ratio = 1.5
        max_attack_ratio = 3
        base_reserve_threshold = 80
        base_reserve_pool_threshold = 10
        base_direct_to_front_chance_out_of_100 = 10
        max_activated_reserves = 140  
        max_activated_direct_reserves = 3
        centers_of_gravity = 0
        turns_to_pull = 0
        center_of_gravity_chance_out_of_100 = 0
        super().__init__(base_attack_chance, base_hostile_count_factor, base_friendly_count_factor, base_defensibility_threshold, min_attack_ratio, max_attack_ratio, base_reserve_threshold, base_reserve_pool_threshold, base_direct_to_front_chance_out_of_100, max_activated_reserves, max_activated_direct_reserves, centers_of_gravity, turns_to_pull, center_of_gravity_chance_out_of_100)

# Sends small packets of reenforcements to the front without waiting for them to "charge" much.
# This makes it a strong pressurer, and it also adapts flexibly to a changing situation.
# It tends to be weak behind the front line, however.
class Water(Personality):
    def __init__(self):   
        self.name = "Water"
        base_attack_chance = 90
        base_hostile_count_factor = .45
        base_friendly_count_factor = .35
        base_defensibility_threshold = 2.5
        min_attack_ratio = 1.5
        max_attack_ratio = 3
        base_reserve_threshold = 10
        base_reserve_pool_threshold = 3
        base_direct_to_front_chance_out_of_100 = 100 
        max_activated_reserves = 140  
        max_activated_direct_reserves = 3
        centers_of_gravity = 0
        turns_to_pull = 0
        center_of_gravity_chance_out_of_100 = 0
        super().__init__(base_attack_chance, base_hostile_count_factor, base_friendly_count_factor, base_defensibility_threshold, min_attack_ratio, max_attack_ratio, base_reserve_threshold, base_reserve_pool_threshold, base_direct_to_front_chance_out_of_100, max_activated_reserves, max_activated_direct_reserves, centers_of_gravity, turns_to_pull, center_of_gravity_chance_out_of_100)

# NOTE: While Water is probably the best of these so far in a uniform 1v1 test where both sides equally control half of
#       the map and have 20 starting ships on each system, it is a close thing between SnappingTurtle and Water
#       sometimes. Meanwhile, Haymaker rarely manages to punch through in that scenario. But that is not the objective
#       measure of which of these is "better". Their real value is in crafting scenario-specific opponents who behave
#       a little differently (which I will explore down the road). All of these hang around a similar "zone" in terms
#       of their front line behavior and mostly differ in how they route reserves (for now). It is easy to make 
#       mixtures of these variables which are simply bad, or which affect performance, while occasionally some are
#       just better than others. These three are the ones that made the cut during manual testing of the latest version.
#       I will do more advanced automated testing in a variety of scenarios down the road, once the AIs have a few more 
#       layers of differentiation in their front-line behavior. For 0.0.5, the AI factions in the first stage use a 
#       mixture of SnappingTurtle and Water, while in the invader stage Haymaker is used. Manual testing is only so
#       useful here, so for 0.0.5 I went with a fairly similar zone of behavior which passed the eyeball test and 
#       was interesting during playtesting. For 0.0.6+ I will be using an automated testing suite to gather a lot more
#       data points to determine which AI personality factors actually matter in which scenarios, and maybe find some
#       novel combinations.

# The main thing Haymaker does is that it will send its directly-waypointed reserves towards a specific "center of
# gravity" along the line, which changes every so often. Water beats this one often in a uniform 1v1, and it's
# primarily for the "invader" scenario. Haymaker tends to be brittle behind the front, but the sudden swinging 
# reenforcement waves can catch you unawares if you are behind the lines and didn't scout it.
class Haymaker(Personality): 
    def __init__(self): 
        self.name = "Haymaker"
        base_attack_chance = 90
        base_hostile_count_factor = .45
        base_friendly_count_factor = .28
        base_defensibility_threshold = 3
        min_attack_ratio = 1.3
        max_attack_ratio = 3
        base_reserve_threshold = 10
        base_reserve_pool_threshold = 3
        base_direct_to_front_chance_out_of_100 = 100
        max_activated_reserves = 140 
        max_activated_direct_reserves = 3
        centers_of_gravity = 1
        turns_to_pull = 100
        center_of_gravity_chance_out_of_100 = 100
        super().__init__(base_attack_chance, base_hostile_count_factor, base_friendly_count_factor, base_defensibility_threshold, min_attack_ratio, max_attack_ratio, base_reserve_threshold, base_reserve_pool_threshold, base_direct_to_front_chance_out_of_100, max_activated_reserves, max_activated_direct_reserves, centers_of_gravity, turns_to_pull, center_of_gravity_chance_out_of_100)

