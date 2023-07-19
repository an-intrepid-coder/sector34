# note: all dimensions hard-coded for now, as the game is assumed to 
#       always be of dimensions (SCREEN_WIDTH, SCREEN_HEIGHT)

from os import path

VERSION = "0.0.2"

FONT_PATH = path.abspath(path.join(path.dirname(__file__), "./sansation/Sansation-Regular.ttf"))
WINDOW_ICON_PATH = path.abspath(path.join(path.dirname(__file__), "./window_icon.png"))

SCREEN_WIDTH_PX = 1100
SCREEN_HEIGHT_PX = 720

FPS = 24

MAP_WIDTH_PX = 800
MAP_HEIGHT_PX = 600

HUD_WIDTH_PX = 300
HUD_HEIGHT_PX = 600
HUD_TICKER_LIMIT = 100
HUD_WIGGLE_FREQUENCY = 4
HUD_CHECKBOX_WIDTH = 20

CONSOLE_FONT_SIZE = 16
CONSOLE_FONT_PADDING_PX = 2
CONSOLE_WIDTH_PX = 1100
CONSOLE_HEIGHT_PX = 120

# "Hard Mode" increases the ship production for AI Empires
HARD_MODE_PRODUCTION_BONUS = 15

# Font sizes
HUD_FONT_SIZE = 19
ETA_LINE_FONT_SIZE = 22
FLEET_OVERLAY_FONT_SIZE = 14
STAR_SYSTEM_FONT_SIZE = 14
FLEET_FONT_SIZE = 14
TACTICAL_MODE_FONT_SIZE = 19
TACTICAL_BATTLE_RESULT_FONT_SIZE = 28
GAME_OVER_SPLASH_FONT_SIZE = 18
VICTORY_SPLASH_FONT_SIZE = 16
LOADING_SCREEN_FONT_SIZE = 40

# The chance to spice up the stock names
# with prefixes and suffixes
SYSTEM_PREFIX_CHANCE_OUT_OF_100 = 1
SYSTEM_SECONDARY_CHANCE_OUT_OF_100 = 5

# NOTE: Reenforcements happen automatically, based on
# on the reenforce_chance_out_of_100 of a given
# system, every turn. Only the player can pool 
# reenforcements and deploy them at will. All other 
# factions spawn reenforcements in place. Player
# and AI homeworlds have a set reenforcement chance,
# while every other system is randomly allocated one
# based on the bounds below.
DEFAULT_HW_REENFORCEMENT_CHANCE_OUT_OF_100 = 50 
DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MIN = 10 
DEFAULT_AI_REENFORCE_CHANCE_OUT_OF_100_MAX = 30 

STAR_RADIUS_PX = 9
# Systems and Fleets use square hit boxes, with some
# extra padding for better clickability.
LOCATION_HITBOX_SIDE_PX = STAR_RADIUS_PX * 2 + 2
FLEET_HITBOX_SIDE_PX = STAR_RADIUS_PX * 2 + 2

NON_SPACEFARING_PRODUCTION_PENALTY = 3

# NOTE: Fleet width is the number of d20s rolled in
#       the contest that decides a round of combat.
#       For every multiple of outnumber margin that
#       a side outnumbers their opponenet by, they
#       get an extra fleet width. A fleet of less
#       than 3 ships only gets its number of ships
#       as fleet width. When outnumbered after the
#       first round of combat, the outnumbered
#       side has a chance to retreat which is
#       the default retreat chance multiplied by
#       how many margins they are outnumbered by,
#       to a maximum of 90%. Retreating ships
#       simply flee to the nearest friendly world.
DEFAULT_FLEET_WIDTH = 3
DEFAULT_OUTNUMBER_MARGIN = .5 
DEFAULT_RETREAT_CHANCE_OUT_OF_100 = 10 
DEFAULT_RETREAT_CHANCE_HARD_CAP = 90 
# NOTE: There is a chance for an outnumbered side to gain
#       LAST STAND or CHARGE. The former gives a bonus to
#       the defender's d20 rolls every round, while the
#       latter gives a bonus to the attacker's and prevents
#       them from retreating. 
LAST_STAND_CHANCE_OUT_OF_100 = 10
LAST_STAND_D20_BONUS = 1
CHARGE_CHANCE_OUT_OF_100 = 10
CHARGE_D20_BONUS = 1
# NOTE: There is a chance every round for a "brilliancy" which
#       gives a bonus to that side's d20 rolls.
BRILLIANCY_CHANCE_OUT_OF_100 = 5
BRILLIANCY_BONUS = 3

# NOTE: All distances calculated ultimately based on pixel distance,
#       where 30px == 4 LY. Will take a slightly different
#       approach when the game migrates to full-screen with a 
#       scrollable/zoomable map.

LY = 4  # pixels

DEFAULT_SPEED_LY = 3

DEFAULT_FUEL_RANGE_LY = 28

MAP_BORDER_SPAWN_PADDING_PX = DEFAULT_SPEED_LY * 2 * LY
STAR_MIN_DISTANCE_LY = 7

LOC_HOVER_MIN_REL_PX = (STAR_MIN_DISTANCE_LY * LY) // 2

DEFAULT_MIN_SENSOR_RANGE_LY = 7
DEFAULT_MAX_SENSOR_RANGE_LY = 28
DEFAULT_HW_SENSOR_RANGE_LY = 42

# Fleets enjoy very good sensor coverage once they are in
# deep space; better than most systems in the game. This
# means that they are useful for scouting.
DEFAULT_FLEET_SENSOR_RANGE_LY = DEFAULT_MAX_SENSOR_RANGE_LY

# The percentage of the starting map
# which are Pirate systems.
PIRATE_DENSITY = .03

# Pirates can raid from off-map:
OFF_MAP_RAID_CHANCE_OUT_OF_100 = 1

# Pirate AI:
PIRATE_OVERMATCH_THRESHOLD = 1.5
PIRATE_RAID_CHANCE_OUT_OF_100 = 5

# NOTE: Currently there are just six,
#       but eventually I will make that
#       variable, along with map size.
NUM_AI_EMPIRES = 6
AI_EMPIRE_FACTION_NAME_SIZE_CONSTRAINT = 10

# The relative size of an incoming fleet for it to be
# considered dangerous by the AI:
INCOMING_THREAT_THRESHOLD = .25

FLEET_ETA_LINE_WIDTH = 3

# NOTE: The player starts with a decisive advantage, but
#       the AI Empires can get quite out of hand if the
#       player isn't careful.
PIRATES_STARTING_SHIPS_MIN = 5
PIRATES_STARTING_SHIPS_MAX = 10
AI_EMPIRE_STARTING_SHIPS = 15
PLAYER_STARTING_SHIPS = 20
NON_SPACEFARING_STARTING_SHIPS_MIN = 1
NON_SPACEFARING_STARTING_SHIPS_MAX = 3
NON_SPACEFARING_PRODUCTION_LIMIT_THRESHOLD = 20

# Empire AI: 
# NOTE: For now, all AI Empires behave the same
#       way. I will individualize them down the
#       road, extensively.
AI_EMPIRE_OVERMATCH_THRESHOLD = 1.5
AI_EMPIRE_EVACUATION_THRESHOLD = 3  # for now
AI_EMPIRE_MIN_ATTACK_RATIO = AI_EMPIRE_OVERMATCH_THRESHOLD
AI_EMPIRE_MAX_ATTACK_RATIO = AI_EMPIRE_EVACUATION_THRESHOLD
BASE_AI_EMPIRE_ATTACK_CHANCE_OUT_OF_100 = 5  # For now...

# The % of systems required for victory condition,
# in addition to destroying all pirates and AI empires
CONQUEST_PERCENT_FOR_VICTORY = 50

# Colors
COLOR_FOG = (70, 70, 70) 
COLOR_SENSOR = (100, 180, 255)
COLOR_FUEL_RANGE = (255, 255, 0)
COLOR_AI_EMPIRE_1 = (0, 0, 255)
COLOR_AI_EMPIRE_2 = (66, 245, 245)
COLOR_AI_EMPIRE_3 = (255, 153, 0) 
COLOR_AI_EMPIRE_4 = (255, 255, 0)
COLOR_AI_EMPIRE_5 = (115, 74, 18)
COLOR_AI_EMPIRE_6 = (255, 0, 255)
COLOR_PLAYER =  (0, 255, 0)
COLOR_PIRATES = (255, 0, 0)
COLOR_NON_SPACEFARING = (140, 140, 140)
COLOR_EXPLOSION = (255, 153, 0)
COLOR_DESTROYER = (120, 120, 120)
COLOR_OCEANS = (0, 0, 100)
COLOR_CONTINENTS_MIN = 40
COLOR_CONTINENTS_MAX = 100
COLOR_CLOUDS_MIN = 40
COLOR_CLOUDS_MAX = 100

STAR_SYSTEM_LINE_WIDTH_PX = 2

ai_empire_colors = [
    COLOR_AI_EMPIRE_1,
    COLOR_AI_EMPIRE_2,
    COLOR_AI_EMPIRE_3,
    COLOR_AI_EMPIRE_4,
    COLOR_AI_EMPIRE_5,
    COLOR_AI_EMPIRE_6,
]

# Starfield Generation
LOCAL_PLANET_MIN_SIZE = 200
LOCAL_PLANET_MAX_SIZE = SCREEN_WIDTH_PX // 2
LOCAL_STAR_MIN_SIZE = 5
LOCAL_STAR_MAX_SIZE = 20
LOCAL_CLOUD_DENSITY = .0120
NUM_CONTINENTS_MIN = 2
NUM_CONTINENTS_MAX = 7
NUM_CONTINENT_POINTS_MIN = 30
NUM_CONTINENT_POINTS_MAX = 50

# Tactical battle stuff
ENGINE_COLOR_1 = (255, 0, 255) 
ENGINE_COLOR_2 = (155, 0, 155) 
TACTICAL_BATTLE_RATE = 60
TACTICAL_BATTLE_COOLDOWN = 6
STARFIELD_DENSITY = .0005
TACTICAL_SCREEN_PADDING_PX = 60
BASE_TACTICAL_SPEED_PX = 1
MOVE_FREQUENCY = 50
DESTROYER_VALUE = 1
DESTROYER_WIDTH = 20
DESTROYER_LENGTH = 36
DESTROYER_LASER_FREQUENCY = 100
DESTROYER_LASER_QUANTITY = 1
TACTICAL_BATTLE_CRITICAL_EXPLOSION_CHANCE_OUT_OF_10000 = 111
EXPLOSION_RADIUS = DESTROYER_LENGTH * 5
INSIGNIA_RADIUS = 2
NUM_EXPLOSION_FRAMES = 12
NUM_EXPLOSION_MARKS = 7 # Will tweak this TODO
LASER_WIDTH = 5
NUM_ENGINE_FRAMES = 2

INTRO_STRINGS = [
    "It has been 100 years since the empire fell...",
    "Sector 34 is a fragmented place. Many of those systems which still have FTL are the bases of raiders and pirates.",
    "The vast majority of systems have lost the means to expand beyond their solar system, but are not helpless. They will grow stronger with time.",
    "Every system in Sector 34 is inhabited by the remnants of the empire, who terraformed every system to include an earth-like world!",
    "Some FTL-capable systems claim to be successors to the empire. Of those, yours is the most powerful and ambitious. Good luck!",
    "To succeed, you must vanquish all the pirates, subjugate all the other would-be 'empires', and control at least 50% of the Sector.",
]

# Debug mode stuff
WATCH_TIMER_RATE = 60
PLAYER_DEBUG_MODE_SHIPS = 800 
AI_EMPIRE_DEBUG_MODE_SHIPS = 800  
PIRATE_DEBUG_MODE_SHIPS = 300
NON_SPACEFARING_DEBUG_MODE_SHIPS = 300

