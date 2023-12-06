import pygame 
from settings import *
from entity import Entity
import math

class Player(Entity):
	def __init__(self,pos,groups,obstacle_sprites, create_attack, destroy_attack, create_magic):
		super().__init__(groups)
		self.image = pygame.transform.scale(pygame.image.load('graphics/player/_Warrior/WalkDown/1.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha()
		self.rect = self.image.get_rect(topleft = pos)
		self.hitbox = self.rect.inflate(0,-26)
		self.is_floor = False
		self.is_wall = False

		# movement
		self.attacking = False
		self.attack_cooldown = 50
		self.status = 'down'
		self.attack_time = None
		self.current_frame = 0
		self.animation_speed = ANIMATION_SPEED

		self.obstacle_sprites = obstacle_sprites
  
		# Load animation frames
		self.animations = {
			'right': [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkRight/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)],
			'left': [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkLeft/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)],
			'up' : [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkUp/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)],
			'down' : [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkDown/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)]
		}
  
		# Weapon
		self.create_attack = create_attack
		self.destroy_attack = destroy_attack
		self.weapon_index = 0
		self.weapon = list(weapon_data.keys())[self.weapon_index]
		self.can_switch_weapon = True
		self.weapon_switch_time = None
		self.switch_duration_cooldown = 200
  
		# magic
		self.create_magic = create_magic
		self.magic_index = 0
		self.magic = list(magic_data.keys())[self.magic_index]
		self.can_switch_magic = True
		self.magic_switch_time = None
  
		# Stats
		self.stats = {'health' : 100, 'energy' : 60, 'attack' : 10, 'magic' : 4, 'speed' : 4}
		self.health = self.stats['health'] 
		self.energy = self.stats['energy'] 
		self.exp = 123
		self.speed = self.stats['speed']

	def animate(self):
		if self.direction.magnitude() != 0:  # Check if the player is moving
			# Progress through animation frames only if moving
			self.current_frame += self.animation_speed
			if self.current_frame >= len(self.animations[self.status]):
				self.current_frame = 0
		else:
			# If not moving, reset to the first frame
			self.current_frame = 0

		self.image = self.animations[self.status][int(self.current_frame)]
	
	def get_full_weapon_damage(self):
		base_damage = self.stats['attack']
		weapon_damage = weapon_data[self.weapon]['damage']
		return base_damage + weapon_damage
 
	def update_direction_based_on_mouse(self):
		mouse_x, mouse_y = pygame.mouse.get_pos()
		screen_center_x = WIDTH // 2
		screen_center_y = HEIGHT // 2

		# Determine the direction based on the mouse's position relative to the screen's center
		if mouse_x > screen_center_x:
			if abs(mouse_x - screen_center_x) > abs(mouse_y - screen_center_y):
				self.status = 'right'
			else:
				self.status = 'up' if mouse_y < screen_center_y else 'down'
		else:
			if abs(mouse_x - screen_center_x) > abs(mouse_y - screen_center_y):
				self.status = 'left'
			else:
				self.status = 'up' if mouse_y < screen_center_y else 'down'
	
	def input(self):
		self.update_direction_based_on_mouse()

		# Movement keys
		keys = pygame.key.get_pressed()
		if not self.attacking:
			if keys[pygame.K_w]:
				self.direction.y = -1
			elif keys[pygame.K_s]:
				self.direction.y = 1
			else:
				self.direction.y = 0

			if keys[pygame.K_d]:
				self.direction.x = 1
			elif keys[pygame.K_a]:
				self.direction.x = -1
			else:
				self.direction.x = 0
   
		# Attack input (left mouse button)
		if pygame.mouse.get_pressed()[0] and not self.attacking:
			self.attacking = True
			self.attack_time = pygame.time.get_ticks()
			self.create_attack()
			print(f'direction while attacking: {self.status}')
			
			print('attack')

		# Magic input (right mouse button)
		if pygame.mouse.get_pressed()[2] and not self.attacking:
			self.attacking = True
			self.attack_time = pygame.time.get_ticks()
			style = list(magic_data.keys())[self.magic_index]
			strength = list(magic_data.values())[self.magic_index]['strength'] + self.stats['magic']
			cost = list(magic_data.values())[self.magic_index]['cost']
			self.create_magic(style, strength, cost)
			print('magic')
   
		# switch weapon
		if keys[pygame.K_e] and self.can_switch_weapon:
			self.can_switch_weapon = False
			self.weapon_switch_time = pygame.time.get_ticks()
			if self.weapon_index < len(list(weapon_data.keys())) - 1:
				self.weapon_index += 1
			else:
				self.weapon_index = 0
			self.weapon = list(weapon_data.keys())[self.weapon_index]

		# switch weapon backward
		if keys[pygame.K_q] and self.can_switch_weapon:
			self.can_switch_weapon = False
			self.weapon_switch_time = pygame.time.get_ticks()
			if self.weapon_index > 0:
				self.weapon_index -= 1
			else:
				self.weapon_index = len(list(weapon_data.keys())) - 1
			self.weapon = list(weapon_data.keys())[self.weapon_index]
   
		# switch magic
		if keys[pygame.K_c] and self.can_switch_magic:
			self.can_switch_magic = False
			self.magic_switch_time = pygame.time.get_ticks()
			if self.magic_index < len(list(magic_data.keys())) - 1:
				self.magic_index += 1
			else:
				self.magic_index = 0
			self.magic = list(magic_data.keys())[self.magic_index]

		# switch magic backward
		if keys[pygame.K_x] and self.can_switch_magic:
			self.can_switch_magic = False
			self.magic_switch_time = pygame.time.get_ticks()
			if self.magic_index > 0:
				self.magic_index -= 1
			else:
				self.magic_index = len(list(magic_data.keys())) - 1
			self.magic = list(magic_data.keys())[self.magic_index]

	def cooldowns(self):
		current_time = pygame.time.get_ticks()
  
		if self.attacking:
			if current_time - self.attack_time >= self.attack_cooldown + weapon_data[self.weapon]['cooldown']:
				self.attacking = False
				self.destroy_attack()

		if not self.can_switch_weapon:
			if current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
				self.can_switch_weapon = True

		if not self.can_switch_magic:
			if current_time - self.magic_switch_time >= self.switch_duration_cooldown:
				self.can_switch_magic = True

	def update(self):
		self.input()
		self.cooldowns()
		if not self.attacking:
			self.move(self.speed)

		self.animate()
