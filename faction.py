from enum import Enum
from constants import *

# TODO: turn this into a full Class

ai_empire_colors = [
    AI_EMPIRE_COLOR_1,
    AI_EMPIRE_COLOR_2,
    AI_EMPIRE_COLOR_3,
    AI_EMPIRE_COLOR_4,
    AI_EMPIRE_COLOR_5,
    AI_EMPIRE_COLOR_6,
]


class Faction(Enum):
    PLAYER = 1
    PIRATES = 2
    NON_SPACEFARING = 3
    AI_EMPIRE_1 = 4
    AI_EMPIRE_2 = 5
    AI_EMPIRE_3 = 6
    AI_EMPIRE_4 = 7
    AI_EMPIRE_5 = 8
    AI_EMPIRE_6 = 9
    EXOGALACTIC_INVASION = 10  # NOTE: Not implemented yet
    # more to come


ai_empire_factions = [Faction.AI_EMPIRE_1, Faction.AI_EMPIRE_2, Faction.AI_EMPIRE_3,
                      Faction.AI_EMPIRE_4, Faction.AI_EMPIRE_5, Faction.AI_EMPIRE_6]


def faction_to_color(faction):
    if faction == Faction.PLAYER:
        return (0, 255, 0)
    elif faction == Faction.PIRATES:
        return (255, 0, 0)
    elif faction == Faction.NON_SPACEFARING:
        return (120, 120, 120)
    elif faction == Faction.AI_EMPIRE_1:
        return ai_empire_colors[0]
    elif faction == Faction.AI_EMPIRE_2:
        return ai_empire_colors[1]
    elif faction == Faction.AI_EMPIRE_3:
        return ai_empire_colors[2]
    elif faction == Faction.AI_EMPIRE_4:
        return ai_empire_colors[3]
    elif faction == Faction.AI_EMPIRE_5:
        return ai_empire_colors[4]
    elif faction == Faction.AI_EMPIRE_6:
        return ai_empire_colors[5]
    return None
