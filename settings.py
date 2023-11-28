import pygame
import random

# game setup
WIDTH    = 1280	
HEIGHT   = 720
FPS      = 60
TILESIZE = 32
SAFETY_MARGIN = 2

# ui
BAR_HEIGHT = 20
HEALTH_BAR_WIDTH = 200
ENERGY_BAR_WIDTH = 140
ITEM_BOX_SIZE = 80
UI_FONT = 'graphics/font/joystix.ttf'
UI_FONT_SIZE = 18

# general colors
WATER_COLOR = '#71ddee'
UI_BG_COLOR = '#222222'
UI_BORDER_COLOR = '#111111'
TEXT_COLOR = '#EEEEEE'

# ui colors
HEALTH_COLOR = 'red'
ENERGY_COLOR = 'blue'
UI_BORDER_COLOR_ACTIVE = 'gold'

# Define the size of the map
MAP_WIDTH = 70
MAP_HEIGHT = 70

# Define Player setup
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40

# weapons
weapon_data = {
    'sword' : {'cooldown': 100, 'damage' : 15, 'graphic' : 'graphics/weapons/sword/full.png'},
    'lance' : {'cooldown': 400, 'damage' : 30, 'graphic' : 'graphics/weapons/lance/full.png'},
    'axe' : {'cooldown': 300, 'damage' : 20, 'graphic' : 'graphics/weapons/axe/full.png'},
    'rapier' : {'cooldown': 50, 'damage' : 8, 'graphic' : 'graphics/weapons/rapier/full.png'},
    'sai' : {'cooldown': 80, 'damage' : 10, 'graphic' : 'graphics/weapons/sai/full.png'},
}

# magic
magic_data = {'flame' : {'strength' : 5, 'cost' : 20, 'graphic' : 'graphics/particles/flame/fire.png'},
              'heal' : {'strength' : 20, 'cost' : 10, 'graphic' : 'graphics/particles/heal/heal.png'}}

# enemy
monster_data = {'Worm' : {'health' : 100, 'damage' : 20, 'attack_type' : 'slash', 'attack_sound' : 'audio/attack/slash.wav', 'speed' : 0, 'resistance' : 3, 'attack_radius' : 30, 'notice_radius' : 360, 'exp' : 100},
                'BigWorm' : {'health' : 100, 'damage' : 20, 'attack_type' : 'claw', 'attack_sound' : 'audio/attack/claw.wav', 'speed' : 0, 'resistance' : 3, 'attack_radius' : 30, 'notice_radius' : 360, 'exp' : 100}, 
                'Skeleton' : {'health' : 100, 'damage' : 20, 'attack_type' : 'thunder', 'attack_sound' : 'audio/attack/fireball.wav', 'speed' : 1, 'resistance' : 3, 'attack_radius' : 30, 'notice_radius' : 360, 'exp' : 100}, 
                'Spider' :  {'health' : 100, 'damage' : 20, 'attack_type' : 'leaf_attack', 'attack_sound' : 'audio/attack/slash.wav', 'speed' : 2, 'resistance' : 3, 'attack_radius' : 30, 'notice_radius' : 360, 'exp' : 100}}