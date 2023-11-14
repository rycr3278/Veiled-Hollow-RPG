import pygame 
from settings import *

class Player(pygame.sprite.Sprite):
	def __init__(self,pos,groups,obstacle_sprites):
		super().__init__(groups)
		self.image = pygame.transform.scale(pygame.image.load('graphics/player/_Warrior/WalkLeft/1.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha()
		self.rect = self.image.get_rect(topleft = pos)
		self.hitbox = self.rect.inflate(0,-26)

		self.direction = pygame.math.Vector2()
		self.speed = 8

		self.obstacle_sprites = obstacle_sprites
  
		# Load animation frames
		self.animations = {
			'right': [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkRight/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)],
			'left': [pygame.transform.scale(pygame.image.load(f'graphics/player/_Warrior/WalkLeft/{i}.png'), (PLAYER_WIDTH, PLAYER_HEIGHT)).convert_alpha() for i in range(1,5)]
		}
  
		self.current_frame = 0
		self.animation_speed = 0.15 # Adjust as needed

	def animate(self):
		direction = self.direction.x

		if direction > 0:
			self.current_frame += self.animation_speed
			if self.current_frame >= len(self.animations['right']):
				self.current_frame = 0
			self.image = self.animations['right'][int(self.current_frame)]

		elif direction < 0:
			self.current_frame += self.animation_speed
			if self.current_frame >= len(self.animations['left']):
				self.current_frame = 0
			self.image = self.animations['left'][int(self.current_frame)]

	
	def input(self):
		keys = pygame.key.get_pressed()

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

	def update(self):
		self.input()
		self.move(self.speed)
	
		# Animate only when moving
		if self.direction.magnitude() != 0:
			self.animate()
		else:
			self.current_frame = 0  # Reset animation frame if not moving