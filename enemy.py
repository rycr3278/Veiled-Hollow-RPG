import pygame
from settings import *
from entity import Entity
import logging
import networkx as nx

logging.basicConfig(filename='game_debug.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

# A* helper functions
def create_graph_from_layout(dungeon_layout):
		G = nx.grid_2d_graph(len(dungeon_layout[0]), len(dungeon_layout), create_using=nx.Graph())
		for y, row in enumerate(dungeon_layout):
			for x, tile in enumerate(row):
				if tile != ' ':  # If the tile is not walkable, remove the node
					G.remove_node((x, y))
		return G

def manhattan_distance(a, b):
		(x1, y1) = a
		(x2, y2) = b
		return abs(x1 - x2) + abs(y1 - y2)




class Enemy(Entity):
	
	id_counter = 0  # Class variable for keeping track of the number of enemies
	
	enemy_frame_data = {
		'Spider': {'frame_size' : (64,64), 'hitbox_scale': 0.6, 'hitbox_offset': (0, 0), 'walk': 8, 'attack': 12, 'death': 17, 'idle': 8, 'hurt' : 6, 'final_death' : 1},
		'Worm': {'frame_size' : (128, 128), 'hitbox_scale': 0.3, 'hitbox_offset': (0, 10), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32, 'final_death' : 1, 'waiting' : 1},
		'Skeleton': {'frame_size' : (128,128), 'hitbox_scale': 0.3, 'hitbox_offset': (0, 10), 'walk': 8, 'attack': 17, 'death': 13, 'idle': 7, 'hurt' : 11, 'final_death' : 1},
		'BigWorm': {'frame_size' : (128, 128), 'hitbox_scale': 0.3, 'hitbox_offset': (0, 10), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32, 'final_death' : 1, 'waiting' : 1}
	}

	def __init__(self, monster_name, pos, groups, obstacle_sprites, dungeon_layout, player):
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
		
		self.is_wandering = False
		self.is_pursuing = False

		# Set initial status based on monster type
		if self.monster_type in ['Worm', 'BigWorm']:
			self.status = 'waiting'
		else:
			self.status = 'idle'
			self.is_wandering = True
			
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
		self.player = player
		self.player_direction = pygame.math.Vector2()
		self.player_distance = 0
		
		# invincibility timer
		self.vulnerable = True
		self.hit_time = None
		self.invincibility_duration = 500
  
		# collision variables
		self.current_path = []  # Store the current A* path
		self.dungeon_layout = dungeon_layout  # Store a reference to the dungeon layout for pathfinding
		self.dungeon_graph = create_graph_from_layout(self.dungeon_layout)
  
		# Initialize the path update time tracking
		self.last_path_update_time = pygame.time.get_ticks()
		self.path_update_interval = 200  # set interval in milliseconds, adjust as needed
  
		# Initialize player position tracking variables
		self.last_player_pos_x, self.last_player_pos_y = pos  # Set to enemy's initial position, or 0,0

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
					self.is_wandering = True

				if action == 'retreat' and self.frame_index == len(self.animations['retreat']) - 1:
					self.status = 'waiting'  # Transition back to 'waiting' after 'retreat'

				# Transition from 'death' to 'final_death'
				if action == 'death' and self.frame_index == len(self.animations['death']) - 1:
					self.status = 'final_death'
					self.is_wandering = False
					self.is_pursuing = False
					
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
				self.direction = pygame.math.Vector2()
				if not self.facing_right:
					self.final_death_image = pygame.transform.flip(self.final_death_image, True, False)

			else:
				self.status = 'hurt'
				self.vulnerable = False
				self.frame_index = 0
				
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
				self.is_wandering = False
				self.is_pursuing = True
			elif distance <= self.notice_radius:
				self.status = 'walk'
				self.is_wandering = False
				self.is_pursuing = True
			elif self.status == 'attack' and self.frame_index == len(self.animations['attack']) - 1:
				self.status = 'walk'
				self.is_wandering = False
				self.is_pursuing = True
			else:

				self.is_wandering = True
				self.is_pursuing = False

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
			elif self.is_pursuing:
				self.update_direction(player)
		
		# Update facing direction
		if self.direction.x < 0:
			self.facing_right = False
		elif self.direction.x > 0:
			self.facing_right = True

	def update_direction(self, player):
			_, direction = self.get_player_distance_direction(player)
			self.direction = direction

	def update_player_info(self, player):
		self.player_direction = self.get_player_distance_direction(player)[1]
		self.player_distance = self.get_player_distance_direction(player)[0]

	def draw_hitbox(self, surface, hitbox_pos, color=(255, 0, 0), width=2):
		# Draw a rectangle around the hitbox for debugging
		pygame.draw.rect(surface, color, (hitbox_pos, self.hitbox.size), width)

	def randomize_movement(self):
		current_time = pygame.time.get_ticks()

		# If currently moving, check if it's time to stop.
		if self.is_moving:
			if current_time - self.move_timer > self.random_move_duration:
				self.is_moving = False
				self.status = 'idle'  # Stop the walking animation
				self.direction = pygame.math.Vector2()  # Stop moving
				self.pause_timer = current_time
				self.random_pause_duration = random.randint(1000, 3000)  # Set pause duration
			else:
				self.status = 'walk'  # Continue the walking animation
		# If not currently moving, check if it's time to start.
		else:
			if current_time - self.pause_timer > self.random_pause_duration:
				self.is_moving = True
				self.move_timer = current_time
				self.random_move_duration = random.randint(1000, 3000)  # Set move duration
				# Choose a random direction
				dx, dy = random.choice([-1, 0, 1]), random.choice([-1, 0, 1])
				if dx != 0 or dy != 0:  # Ensure it's not a zero vector
					self.direction = pygame.math.Vector2(dx, dy).normalize()
				else:
					self.direction = pygame.math.Vector2(dx, dy)  # Keep as zero vector if both dx and dy are 0

	def check_collision(self, dx, dy):
		# Adjust the enemy's position if a collision is detected
		new_position = pygame.Rect(self.rect.x + dx, self.rect.y + dy, self.rect.width, self.rect.height)
		for sprite in self.obstacle_sprites:
			if new_position.colliderect(sprite.rect):
				logging.debug(f"Enemy {self.id} Collision detected at {new_position}")
				return False  # Collision detected
		return True  # No collision

# A* algo implementation

	def calculate_path(self, target):
		# Convert positions to grid coordinates
		grid_start = (self.rect.centerx // TILESIZE, self.rect.centery // TILESIZE)
		grid_end = (target.rect.centerx // TILESIZE, target.rect.centery // TILESIZE)

		try:
			# Use NetworkX A* algorithm
			raw_path = nx.astar_path(self.dungeon_graph, grid_start, grid_end, heuristic=manhattan_distance)
			self.current_path = self.smooth_path(raw_path)
		except nx.NetworkXNoPath:
			self.current_path = []  # No path found

	def should_update_path(self, player):
		# Define conditions for updating the path
		player_pos = (player.rect.centerx // TILESIZE, player.rect.centery // TILESIZE)
		last_player_pos = (self.last_player_pos_x // TILESIZE, self.last_player_pos_y // TILESIZE)
		if player_pos != last_player_pos and self.is_pursuing:
			logging.debug(f"Enemy {self.id} recalculating path due to player movement")
			self.last_player_pos_x, self.last_player_pos_y = player.rect.centerx, player.rect.centery
			return True
		return False

	def follow_path(self, player):
		if not self.current_path or self.at_path_end():
			self.calculate_path(player)

		if self.current_path:
			next_point = self.current_path[0]
			next_x, next_y = next_point[0] * TILESIZE, next_point[1] * TILESIZE

			# Move towards the next point
			if not self.move_towards(next_x, next_y):
				# If blocked or unable to move, use direction towards player
				distance, direction = self.get_player_distance_direction(player)
				self.direction = direction

	def at_path_end(self):
		# Check if the enemy is at the end of the current path
		if self.current_path:
			last_point = self.current_path[-1]
			last_x, last_y = last_point[0] * TILESIZE, last_point[1] * TILESIZE
			path_end = self.rect.centerx == last_x and self.rect.centery == last_y
			if path_end:
				logging.debug(f'Enemy {self.id} at path end')
		return path_end

	def move_towards(self, target_x, target_y):
		dx, dy = 0, 0
		if self.rect.centerx < target_x:
			dx = self.speed
		elif self.rect.centerx > target_x:
			dx = -self.speed

		if self.rect.centery < target_y:
			dy = self.speed
		elif self.rect.centery > target_y:
			dy = -self.speed

		# Check for collision
		if self.check_collision(dx, dy):
			self.rect.x += dx
			self.rect.y += dy
			
		logging.debug(f"Enemy {self.id} Moving from {self.rect.topleft} towards ({target_x}, {target_y})")

	def smooth_path(self, path):
		"""
		Smooths a path by connecting non-adjacent nodes if there are no obstacles between them.
		"""
		if len(path) <= 2:
			return path

		smooth_path = [path[0]]  # Start with the first node
		i = 0
		while i < len(path) - 1:
			for j in range(len(path) - 1, i, -1):
				if self.line_of_sight(path[i], path[j]):
					# Direct path to a further node is possible
					smooth_path.append(path[j])
					i = j  # Skip to the node with line of sight
					break
			else:
				# If no direct path, go to the next node in the original path
				smooth_path.append(path[i + 1])
				i += 1
		logging.debug(f"Enemy {self.id} Raw path: {path}")
		logging.debug(f"Enemy {self.id} Smoothed path: {smooth_path}")
		return smooth_path

	def line_of_sight(self, start, end):
		"""
		Checks if there's a direct line of sight (no obstacles) between two points.
		"""
		# Calculate increments or steps for checking
		steps = max(abs(start[0] - end[0]), abs(start[1] - end[1]))
		x_step = (end[0] - start[0]) / steps
		y_step = (end[1] - start[1]) / steps

		for i in range(1, steps):
			check_x = start[0] + i * x_step
			check_y = start[1] + i * y_step

			# Check if the position is blocked by an obstacle
			if self.is_blocked(check_x, check_y):
				return False

		return True

	def is_blocked(self, x, y):
		"""
		Checks if a specific point in the grid is blocked by an obstacle.
		"""
		# Convert to tile coordinates and check for obstacles
		grid_x, grid_y = int(x // TILESIZE), int(y // TILESIZE)
		blocked = self.dungeon_layout[grid_y][grid_x] != ' '
  
		return blocked

	def get_player_distance_direction(self, player):
		enemy_vec = pygame.math.Vector2(self.rect.center)
		player_vec = pygame.math.Vector2(player.rect.center)
		distance = (player_vec - enemy_vec).magnitude()
		direction = (player_vec - enemy_vec).normalize() if distance > 0 else pygame.math.Vector2()
		return distance, direction

	def execute_movement(self):
		
		if self.is_pursuing and self.current_path:
			self.follow_path(self.player)
		elif self.is_wandering:
			self.randomize_movement()

		# Movement with collision handling
		dx = self.direction.x * self.speed
		dy = self.direction.y * self.speed
		self.move(dx, dy)  # Now call the move method with updated dx and dy

		# Update facing direction
		if self.direction.x < 0:
			self.facing_right = False
		elif self.direction.x > 0:
			self.facing_right = True

	def move(self, dx, dy):
		if self.direction.magnitude() != 0:
			self.direction = self.direction.normalize()

		self.hitbox.x += dx
		self.collision('horizontal')
		self.hitbox.y += dy
		self.collision('vertical')
		self.rect.center = self.hitbox.center

	def update(self):
     
		if self.status in ['death', 'final_death', 'attack', 'hurt']:
			self.animate()  # Still update animation to ensure death animation plays
			return

		self.update_player_info(self.player)
		self.actions(self.player)
		
		current_time = pygame.time.get_ticks()
		if self.is_pursuing:
			if current_time - self.last_path_update_time > self.path_update_interval or self.should_update_path(self.player):
				self.calculate_path(self.player)
				self.last_path_update_time = current_time
	
		self.execute_movement()		
		self.cooldowns()
		self.check_death()
		self.animate()
		
	def enemy_update(self, player):
		
		if self.status not in ['final_death', 'death']:
			self.get_status(player)
			self.actions(player)
			
			
		self.check_death()

		self.check_death()
		