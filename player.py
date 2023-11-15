import pygame 
from settings import *

class Player(pygame.sprite.Sprite):
	def __init__(self,pos,groups,obstacle_sprites, create_attack, destroy_attack):
		super().__init__(groups)
		self.image = pygame.transform.scale(pygame.image.load('graphics/player/_Warrior/WalkLeft/1.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha()
		self.rect = self.image.get_rect(topleft = pos)
		self.hitbox = self.rect.inflate(0,-26)

		# movement
		self.direction = pygame.math.Vector2()
		self.attacking = False
		self.attack_cooldown = 400
		self.status = 'down'
		self.attack_time = None

		self.obstacle_sprites = obstacle_sprites
  
		# Load animation frames
		self.animations = {
			'right': [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkRight/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)],
			'left': [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkLeft/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)],
			'up' : [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkUp/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)],
			'down' : [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkDown/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)]
		}
  
		self.current_frame = 0
		self.animation_speed = 0.12 # Adjust as needed

		# Weapon
		self.create_attack = create_attack
		self.destroy_attack = destroy_attack
		self.weapon_index = 0
		self.weapon = list(weapon_data.keys())[self.weapon_index]
		self.can_switch_weapon = True
		self.weapon_switch_time = None
		self.switch_duration_cooldown = 200
		print(self.weapon)
  
		# Stats
		self.stats = {'health' : 100, 'energy' : 60, 'attack' : 10, 'magic' : 4, 'speed' : 6}
		self.health = self.stats['health']
		self.energy = self.stats['energy']
		self.exp = 123
		self.speed = self.stats['speed']

	def animate(self):
		direction_x = self.direction.x
		direction_y = self.direction.y

		if direction_x > 0:
			self.current_frame += self.animation_speed
			if self.current_frame >= len(self.animations['right']):
				self.current_frame = 0
			self.image = self.animations['right'][int(self.current_frame)]

		elif direction_x < 0:
			self.current_frame += self.animation_speed
			if self.current_frame >= len(self.animations['left']):
				self.current_frame = 0
			self.image = self.animations['left'][int(self.current_frame)]

		elif direction_y < 0:
			self.current_frame += self.animation_speed
			if self.current_frame >= len(self.animations['up']):
				self.current_frame = 0
			self.image = self.animations['up'][int(self.current_frame)]
   
		elif direction_y > 0:
			self.current_frame += self.animation_speed
			if self.current_frame >= len(self.animations['down']):
				self.current_frame = 0
			self.image = self.animations['down'][int(self.current_frame)]
	
	def input(self):
		keys = pygame.key.get_pressed()

		if keys[pygame.K_w]:
			self.status = 'up'
			self.direction.y = -1
		elif keys[pygame.K_s]:
			self.status = 'down'
			self.direction.y = 1
		else:
			self.direction.y = 0

		if keys[pygame.K_d]:
			self.status = 'right'
			self.direction.x = 1
		elif keys[pygame.K_a]:
			self.status = 'left'
			self.direction.x = -1
		else:
			self.direction.x = 0
   
		# Attack input
		if keys[pygame.K_SPACE] and not self.attacking:
			self.attacking = True
			self.attack_time = pygame.time.get_ticks()
			self.create_attack()
			print('attack')

		# Magic input
		if keys[pygame.K_LCTRL] and not self.attacking:
			self.attacking = True
			self.attack_time = pygame.time.get_ticks()
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

	def move(self,speed):
		if self.direction.magnitude() != 0:
			self.direction = self.direction.normalize()

		self.hitbox.x += self.direction.x * speed
		self.collision('horizontal')
		self.hitbox.y += self.direction.y * speed
		self.collision('vertical')
		self.rect.center = self.hitbox.center

	def collision(self,direction):
		if direction == 'horizontal':
			for sprite in self.obstacle_sprites:
				if sprite.hitbox.colliderect(self.hitbox):
					if self.direction.x > 0: # moving right
						self.hitbox.right = sprite.hitbox.left
					if self.direction.x < 0: # moving left
						self.hitbox.left = sprite.hitbox.right

		if direction == 'vertical':
			for sprite in self.obstacle_sprites:
				if sprite.hitbox.colliderect(self.hitbox):
					if self.direction.y > 0: # moving down
						self.hitbox.bottom = sprite.hitbox.top
					if self.direction.y < 0: # moving up
						self.hitbox.top = sprite.hitbox.bottom

	def cooldowns(self):
		current_time = pygame.time.get_ticks()
  
		if self.attacking:
			if current_time - self.attack_time >= self.attack_cooldown:
				self.attacking = False
				self.destroy_attack()

		if not self.can_switch_weapon:
			if current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
				self.can_switch_weapon = True

	def update(self):
		self.input()
		self.cooldowns()
		self.move(self.speed)
	
		# Animate only when moving
		if self.direction.magnitude() != 0:
			self.animate()
		else:
			self.current_frame = 0  # Reset animation frame if not moving
	
		# Animate only when moving
		if self.direction.magnitude() != 0:
			self.animate()
		else:
			self.current_frame = 0  # Reset animation frame if not moving