class BattleGraph: 
    def __init__(self, atk_ships, def_ships):
        self.starting_ships = {"attacker": atk_ships, "defender": def_ships}
        self.ships_by_side_per_round = [self.starting_ships] # dicts
        self.outnumber_dice_by_side_per_round = [] # dicts
        self.brilliancies_by_side_per_round = [] # dicts
        self.fleet_width_per_round = [] # ints
        self.colors = {}
        self.xp_bonuses = {}
        self.charge = False
        self.last_stand = False
        self.battle_name = None
        self.battle_turn = 0
        
