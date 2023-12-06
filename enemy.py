import pygame
from settings import *
from entity import Entity
import logging


logging.basicConfig(filename='game_debug.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


class Enemy(Entity):
	
	id_counter = 0  # Class variable for keeping track of the number of enemies
	
	enemy_frame_data = {
		'Spider': {'frame_size' : (64,64), 'hitbox_scale': 0.6, 'hitbox_offset': (0, 0), 'walk': 8, 'attack': 12, 'death': 17, 'idle': 8, 'hurt' : 6, 'final_death' : 1},
		'Worm': {'frame_size' : (128, 128), 'hitbox_scale': 0.3, 'hitbox_offset': (0, 10), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32, 'final_death' : 1, 'waiting' : 1},
		'Skeleton': {'frame_size' : (128,128), 'hitbox_scale': 0.3, 'hitbox_offset': (0, 10), 'walk': 8, 'attack': 17, 'death': 13, 'idle': 7, 'hurt' : 11, 'final_death' : 1},
		'BigWorm': {'frame_size' : (128, 128), 'hitbox_scale': 0.3, 'hitbox_offset': (0, 10), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32, 'final_death' : 1, 'waiting' : 1}
	}

	def __init__(self, monster_name, pos, groups, obstacle_sprites):
		super().__init__(groups)
		self.id = Enemy.id_counter  # Assign an ID to the enemy
		Enemy.id_counter += 1  # Increment the counter
		self.sprite_type = 'enemy'
		self.facing_right = True
		self.facing_right_at_death = True
		self.attacking = False
		self.display_surface = pygame.display.get_surface()

		# Determine hitbox size and offset based on enemy type
		enemy_type = monster_name.split('/')[0]
		self.monster_type = enemy_type
		frame_data = self.enemy_frame_data[enemy_type]
		frame_width, frame_height = frame_data['frame_size']
		hitbox_scale_factor = frame_data['hitbox_scale']
		hitbox_x_offset, hitbox_y_offset = frame_data['hitbox_offset']

		# Graphics setup
		self.import_graphics(monster_name)  # Import graphics first
		self.frame_index = 0
		
		# Set initial status based on monster type
		if self.monster_type in ['Worm', 'BigWorm']:
			self.status = 'waiting'
		else:
			self.status = 'idle'
			
		self.image = self.animations[self.status][0]

		# Set initial image and rect
		self.image = self.animations[self.status][self.frame_index]
		self.rect = self.image.get_rect(topleft=pos)
		
		print(f"{self.monster_type} {self.id} Image Position: {self.rect.topleft}")
		
		# Animation setup
		self.last_update = pygame.time.get_ticks()
		
		# Movement
		self.rect = self.image.get_rect(topleft = pos)
		self.move_timer = 0
		self.pause_timer = 0
		self.is_moving = True
		
		self.random_move_duration = random.randint(1000, 3000)  # Duration for moving
		self.random_pause_duration = random.randint(1000, 3000)  # Duration for pausing

		# Add a timer for AI updates to reduce frequency
		self.ai_update_timer = 0
		self.ai_update_interval = 500  # Update AI every 500ms

		# Adjust hitbox size and position
		hitbox_width = int(frame_width * hitbox_scale_factor)
		hitbox_height = int(frame_height * hitbox_scale_factor)
		self.hitbox = pygame.Rect(0, 0, hitbox_width, hitbox_height)
		self.hitbox.center = (self.rect.centerx + hitbox_x_offset, self.rect.centery + hitbox_y_offset)
		
		print(f"{self.monster_type} {self.id} Hitbox Position: {self.hitbox.topleft}")
		
		self.obstacle_sprites = obstacle_sprites
		
		# Stats
		monster_info = monster_data[enemy_type]
		self.health = monster_info['health']
		self.exp = monster_info['exp']
		self.speed = monster_info['speed']
		self.attack_damage = monster_info['damage']
		self.resistance = monster_info['resistance']
		self.attack_radius = monster_info['attack_radius']
		self.notice_radius = monster_info['notice_radius']
		self.attack_type = monster_info['attack_type']
		
		# Player Interaction
		self.can_attack = True
		
		# invincibility timer
		self.vulnerable = True
		self.hit_time = None
		self.invincibility_duration = 500
	   
	def import_graphics(self, name):
		self.animations = {'walk': [], 'waiting' : [], 'hurt': [], 'attack': [], 'death': [], 'idle': [], 'retreat': [], 'final_death' : []}  # Actions
		
		enemy_type = name.split('/')[0]
		frame_width, frame_height = self.enemy_frame_data[enemy_type]['frame_size']

		for action in self.animations.keys():
			try:
				num_frames = self.enemy_frame_data[name.split('/')[0]][action]
				action_sprite_sheet = pygame.image.load(f'graphics/_Crypt/Characters/{name}/{action}.png').convert_alpha()

				for i in range(num_frames):
					x = i * frame_width
					y = 0
					frame = self.get_image(action_sprite_sheet, x, y, frame_width, frame_height)
					self.animations[action].append(frame)
			except KeyError:
				print('this action does not exist')
				# This action does not exist for this enemy type, so we skip it
				pass
   
	def get_image(self, sheet, x, y, width, height):
		# Extracts and returns an image from a sprite sheet
		image = pygame.Surface((width, height), pygame.SRCALPHA)
		image.blit(sheet, (0,0), (x, y, width, height))
		return image
	
	def animate(self):
		now = pygame.time.get_ticks()
		action = self.status

		if action == 'final_death':
			return  # Exit to prevent further animation

		if action in self.animations and len(self.animations[action]) > 0:
			if now - self.last_update >= self.animation_speed * 1000:
				self.last_update = now
				self.frame_index = (self.frame_index + 1) % len(self.animations[action])
				self.image = self.animations[action][self.frame_index]
				if not self.facing_right:
					self.image = pygame.transform.flip(self.image, True, False)

				if action == 'hurt' and self.frame_index == len(self.animations['hurt']) - 1:
					self.status = 'idle'

				if action == 'retreat' and self.frame_index == len(self.animations['retreat']) - 1:
					self.status = 'waiting'  # Transition back to 'waiting' after 'retreat'

				# Transition from 'death' to 'final_death'
				if action == 'death' and self.frame_index == len(self.animations['death']) - 1:
					self.status = 'final_death'
					
	def get_damage(self, player, attack_type):
		current_time = pygame.time.get_ticks()
		
		# Check if the enemy is a worm and if its status is 'waiting'
		if self.monster_type in ['Worm', 'BigWorm'] and (self.status == 'waiting' or self.status == 'death' or (self.status == 'attack' and self.frame_index <= 14) or (self.status == 'retreat' and self.frame_index >= 14)):
			# If the status is 'waiting', do not proceed with taking damage
			return
		
		if self.vulnerable:
			self.direction = self.get_player_distance_direction(player)[1]
			if attack_type == 'weapon':
				self.health -= player.get_full_weapon_damage()
			else:
				pass # magic damage later
			
			self.hit_time = current_time
			self.vulnerable = False
			
			if self.health <= 0:
				self.status = 'death'
				self.frame_index = 0
				self.final_death_image = self.animations['final_death'][0]
				print('self.facing_right: ', self.facing_right)
				print('self.facing_right_at_death: ', self.facing_right_at_death)
				if not self.facing_right:
					self.final_death_image = pygame.transform.flip(self.final_death_image, True, False)
				print("Enemy hit: status set to 'death'")
			else:
				self.status = 'hurt'
				self.vulnerable = False
				self.frame_index = 0
				print(f"get_damage: Enemy hurt, setting status to 'hurt', frame index reset to {self.frame_index}")
				print(self.status)
				
	def cooldowns(self):
		current_time = pygame.time.get_ticks()
		if not self.can_attack:
			if current_time - self.attack_time >= self.attack_cooldown:
				self.can_attack = True
				
		if not self.vulnerable:
			if current_time - self.hit_time >= self.invincibility_duration:
				self.vulnerable = True
	 
	def check_death(self):
		if self.health <= 0 and self.status != 'final_death':
			if self.status != 'death':
				self.status = 'death'
				self.frame_index = 0  # Start at the first frame of the death animation

	def get_player_distance_direction(self, player):
		enemy_vec = pygame.math.Vector2(self.rect.center)
		player_vec = pygame.math.Vector2(player.rect.center)
		distance = (player_vec - enemy_vec).magnitude()
		
		if distance > 0:
			direction = (player_vec - enemy_vec).normalize()
		else:
			direction = pygame.math.Vector2()     
		return (distance, direction)

	def get_status(self, player):
		distance, _ = self.get_player_distance_direction(player)

		if self.monster_type in ['Worm', 'BigWorm']:
			if self.status == 'waiting' and distance <= self.attack_radius:
				self.status = 'attack'
				self.frame_index = 0  # Reset frame index when starting attack

			elif self.status == 'attack':
				if self.frame_index == len(self.animations['attack']) - 1:
					if distance > self.attack_radius:
						self.status = 'retreat'
						self.frame_index = 0
					else:
						self.status = 'idle'

			elif self.status == 'idle':
				# Decide what to do after 'idle' based on player distance
				if distance <= self.attack_radius:
					self.status = 'idle'
				else:
					self.status = 'retreat'
					self.frame_index = 0

			elif self.status == 'retreat' and self.frame_index == len(self.animations['retreat']) - 1:
				self.status = 'waiting'  # Go back to 'waiting' after 'retreat'
	
		else:
			# Handling for other enemy types
			if self.status == 'hurt':
				return
			if distance <= self.attack_radius and self.can_attack:
				self.status = 'attack'
			elif distance <= self.notice_radius:
				self.status = 'walk'
			else:
				self.status = 'idle'

	def actions(self, player):
		if self.status in ['death', 'final_death']:
			return

		if self.monster_type in ['Worm', 'BigWorm']:
			# Special handling for worms
			if self.status not in ['waiting', 'hurt']:
				self.update_direction(player)
		else:
			# Handling for other enemy types
			if self.status in ['hurt', 'attack']:
				self.direction = pygame.math.Vector2()  # Stop moving when attacking
			elif self.status == 'walk':
				self.update_direction(player)
		
		# Update facing direction
		if self.direction.x < 0:
			self.facing_right = False
		elif self.direction.x > 0:
			self.facing_right = True

	def update_direction(self, player):
			_, direction = self.get_player_distance_direction(player)
			self.direction = direction

	def move_and_face_direction(self):
		if self.status not in ['attack', 'death', 'final_death']:
			before_move = f"Before Move [ID: {self.id}]: {self.rect.topleft}"
			before_moving = f"[ID: {self.id}] Moving - Direction: {self.direction}, Speed: {self.speed}"
			x_before_move, y_before_move = self.rect.topleft
			self.move(self.speed)
			after_move = f"After Move [ID: {self.id}]: {self.rect.topleft}"
			x_after_move, y_after_move = self.rect.topleft
			if abs(x_before_move - x_after_move) > 50 or abs(y_before_move - y_after_move) > 50:
				print('it happened')
				print(before_move)
				print(before_moving)
				print(after_move)
				print('Status: ', self.status)

			
			
			# Update facing direction
			if self.direction.x < 0:
				self.facing_right = False
			elif self.direction.x > 0:
				self.facing_right = True

	
		current_time = pygame.time.get_ticks()

		if self.is_moving:
			if current_time - self.move_timer > self.random_move_duration:
				self.is_moving = False
				self.pause_timer = current_time
				self.direction = pygame.math.Vector2()  # Stop moving
				self.random_pause_duration = random.randint(1000, 3000)  # Reset pause duration
		else:
			if current_time - self.pause_timer > self.random_pause_duration:
				self.is_moving = True
				self.move_timer = current_time
				# Move in a random direction
				dx, dy = random.choice([-1, 0, 1]), random.choice([-1, 0, 1])
				if dx != 0 or dy != 0:  # Ensure it's not a zero vector
					self.direction = pygame.math.Vector2(dx, dy).normalize()
				else:
					self.direction = pygame.math.Vector2(dx, dy)  # Keep as zero vector if both dx and dy are 0
				self.random_move_duration = random.randint(1000, 3000)  # Reset move duration

	def draw_hitbox(self, surface, hitbox_pos, color=(255, 0, 0), width=2):
		# Draw a rectangle around the hitbox for debugging
		pygame.draw.rect(surface, color, (hitbox_pos, self.hitbox.size), width)

	def move_and_avoid_obstacles(self):
		# Check for potential collision
		new_position = self.rect.center + self.direction * self.speed
		future_hitbox = self.hitbox.copy()
		future_hitbox.center = new_position

		for sprite in self.obstacle_sprites:
			if future_hitbox.colliderect(sprite.rect):
				self.reverse_direction()
				break

		self.rect.center += self.direction * self.speed

	def reverse_direction(self):
		self.direction.x *= -1
		self.direction.y *= -1

	def adjust_direction_away_from_obstacle(self, obstacle_rect):
		if obstacle_rect.collidepoint(self.rect.midleft):
			self.direction.x = 1
		elif obstacle_rect.collidepoint(self.rect.midright):
			self.direction.x = -1
		if obstacle_rect.collidepoint(self.rect.midtop):
			self.direction.y = 1
		elif obstacle_rect.collidepoint(self.rect.midbottom):
			self.direction.y = -1

	def randomize_movement(self):
		current_time = pygame.time.get_ticks()
		if self.is_moving:
			if current_time - self.move_timer > random.randint(1000, 3000):
				self.is_moving = False
				self.pause_timer = current_time
		else:
			if current_time - self.pause_timer > random.randint(1000, 3000):
				self.is_moving = True
				self.move_timer = current_time
				self.direction = pygame.math.Vector2(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
				if self.direction.length() > 0:
					self.direction = self.direction.normalize()

	def update(self):
		self.randomize_movement()
		
		if self.status != 'final_death':
			if self.status != 'hurt':
				self.move_and_face_direction()  # Handle movement and facing direction
			self.animate()
			
		else:
			if self.facing_right:
				self.image = self.animations['final_death'][0]  # Show the final death frame
			else:
				self.image = pygame.transform.flip(self.animations['final_death'][0], True, False)  # Flip if needed

		self.cooldowns()
		self.check_death()
		
	def enemy_update(self, player):
		
		if self.status not in ['final_death', 'death']:
			self.get_status(player)
			self.actions(player)
			
			
		self.check_death()
		