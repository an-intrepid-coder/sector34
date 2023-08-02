from enum import Enum
from constants import *


class FactionType(Enum):
    PLAYER = 1
    PIRATES = 2
    NON_SPACEFARING = 3
    AI_EMPIRE_1 = 4
    AI_EMPIRE_2 = 5
    AI_EMPIRE_3 = 6
    AI_EMPIRE_4 = 7
    AI_EMPIRE_5 = 8
    AI_EMPIRE_6 = 9
    EXOGALACTIC_INVASION = 10  
    # more to come

ai_empire_faction_types = [FactionType.AI_EMPIRE_1, FactionType.AI_EMPIRE_2, FactionType.AI_EMPIRE_3,
                           FactionType.AI_EMPIRE_4, FactionType.AI_EMPIRE_5, FactionType.AI_EMPIRE_6,
                           FactionType.EXOGALACTIC_INVASION]

def faction_type_to_color(faction):
    if faction == FactionType.PLAYER:
        return COLOR_PLAYER
    elif faction == FactionType.PIRATES:
        return COLOR_PIRATES
    elif faction == FactionType.NON_SPACEFARING:
        return COLOR_NON_SPACEFARING
    elif faction == FactionType.AI_EMPIRE_1:
        return ai_empire_colors[0]
    elif faction == FactionType.AI_EMPIRE_2:
        return ai_empire_colors[1]
    elif faction == FactionType.AI_EMPIRE_3:
        return ai_empire_colors[2]
    elif faction == FactionType.AI_EMPIRE_4:
        return ai_empire_colors[3]
    elif faction == FactionType.AI_EMPIRE_5:
        return ai_empire_colors[4]
    elif faction == FactionType.AI_EMPIRE_6:
        return ai_empire_colors[5]
    elif faction == FactionType.EXOGALACTIC_INVASION:
        return ai_empire_colors[6]
    return None

