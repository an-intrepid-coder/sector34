# NOTE: All dimensions hard-coded for now, as the game is assumed to 
#       always be of dimensions (SCREEN_WIDTH, SCREEN_HEIGHT)

from os import path

VERSION = "0.0.1"

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

# Font sizes
HUD_FONT_SIZE = 19
ETA_LINE_FONT_SIZE = 22
FLEET_OVERLAY_FONT_SIZE = 14
STAR_SYSTEM_FONT_SIZE = 14
FLEET_FONT_SIZE = 14
TACTICAL_MODE_FONT_SIZE = 20
TACTICAL_BATTLE_RESULT_FONT_SIZE = 32
GAME_OVER_SPLASH_FONT_SIZE = 18
VICTORY_SPLASH_FONT_SIZE = 16

# The chance to spice up the stock names
# with prefixes and suffixes
SYSTEM_PREFIX_CHANCE_OUT_OF_100 = 5
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
# Systems and Fleets use square hit boxes
LOCATION_HITBOX_SIDE_PX = STAR_RADIUS_PX * 2 + 3
FLEET_HITBOX_SIDE_PX = STAR_RADIUS_PX * 2 + 3

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

# NOTE: All distances calculated ultimately based on pixel distance,
#       where 1 ISF == 30px == 7 LY. Will take a slightly different
#       approach when the game migrates to full-screen with a 
#       scrollable/zoomable map.

LY = 4  # pixels

DEFAULT_SPEED_LY = 3

DEFAULT_FUEL_RANGE_LY = 28

MAP_BORDER_SPAWN_PADDING_PX = 20
STAR_MIN_DISTANCE_LY = DEFAULT_SPEED_LY * 2 + 2

# NOTE: For now, only the player is affected
#       by sensor ranges. The AI makes all
#       current decisions based on fuel range
#       alone. This is a small advantage for the
#       AI and I will have them abide by sensor
#       ranges soon.
DEFAULT_MIN_SENSOR_RANGE_LY = 7
DEFAULT_MAX_SENSOR_RANGE_LY = 28
DEFAULT_HW_SENSOR_RANGE_LY = 42

# Fleets enjoy very good sensor coverage once they are in
# deep space; better than most systems in the game. This
# means that they are useful for scouting.
DEFAULT_FLEET_SENSOR_RANGE_LY = DEFAULT_MAX_SENSOR_RANGE_LY

# The percentage of the starting map
# which are Pirate systems.
PERCENT_MAP_PIRATES = 10

# Pirate AI:
PIRATE_OVERMATCH_THRESHOLD = 1.5
PIRATE_RAID_CHANCE_OUT_OF_100 = 5

# NOTE: Currently the map generation scheme 
#       requires exactly six AI empires,
#       but eventually I will make that
#       variable, along with map size.
NUM_AI_EMPIRES = 6

# The relative size of an incoming fleet for it to be
# considered dangerous by the AI:
INCOMING_THREAT_THRESHOLD = .25

FLEET_ETA_LINE_WIDTH = 3

# NOTE: The player starts with a decisive advantage, but
#       the AI Empires can get quite out of hand if the
#       player isn't careful.
PIRATES_STARTING_SHIPS = 3
AI_EMPIRE_STARTING_SHIPS = 3
PLAYER_STARTING_SHIPS = 10
NON_SPACEFARING_STARTING_SHIPS = 1

# Empire AI: 
# NOTE: For now, all AI Empires behave the same
#       way. I will individualize them down the
#       road, extensively.
DEFENSIVE_POSTURE_CHANCE_OUT_OF_100 = 75
AI_EMPIRE_OVERMATCH_THRESHOLD = 1.2
AI_EMPIRE_ATTACK_CHANCE_OUT_OF_100 = 3
AI_EMPIRE_SHUFFLE_CHANCE_OUT_OF_100 = 5
AI_EMPIRE_SHUFFLE_RESERVE_MIN = 3

# The % of systems required for victory condition,
# in addition to destroying all pirates and AI empires
CONQUEST_PERCENT_FOR_VICTORY = 50

# Colors
COLOR_FOG = (70, 70, 70) 
COLOR_SENSOR = (100, 180, 255)
COLOR_FUEL_RANGE = (255, 255, 0)
AI_EMPIRE_COLOR_1 = (0, 0, 255)
AI_EMPIRE_COLOR_2 = (66, 245, 245)
AI_EMPIRE_COLOR_3 = (255, 179, 80)
AI_EMPIRE_COLOR_4 = (255, 255, 0)
AI_EMPIRE_COLOR_5 = (255, 255, 255)
AI_EMPIRE_COLOR_6 = (255, 0, 255)

# Tactical battle stuff
TACTICAL_BATTLE_RATE = 50
TACTICAL_BATTLE_COOLDOWN = 5
STARFIELD_DENSITY = .0007
TACTICAL_SCREEN_PADDING_PX = 60
BASE_TACTICAL_SPEED_PX = 1
MOVE_FREQUENCY = 20
DESTROYER_VALUE = 1
DESTROYER_WIDTH = 8
DESTROYER_LENGTH = 16
DESTROYER_LASER_FREQUENCY = 50
DESTROYER_LASER_QUANTITY = 1
