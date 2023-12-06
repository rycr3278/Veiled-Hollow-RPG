
import pygame 
from settings import *
from tile import Tile
from player import Player
from debug import debug
import random
from weapon import Weapon
from ui import UI
from enemy import Enemy
import numpy as np
from scipy.spatial import Delaunay
import networkx as nx

def create_delaunay_triangulation(rooms):
	points = np.array([(room.rect.centerx, room.rect.centery) for room in rooms])
	return Delaunay(points)

def create_mst(triangles):
	edges = set()
	for simplex in triangles.simplices:
		edges.add((simplex[0], simplex[1]))
		edges.add((simplex[1], simplex[2]))
		edges.add((simplex[2], simplex[0]))

	G = nx.Graph(list(edges))
	return nx.minimum_spanning_tree(G)

def add_extra_edges_to_mst(mst, delaunay_tri, percentage=0.05):
	# Extract edges from Delaunay triangulation
	delaunay_edges = set()
	for simplex in delaunay_tri.simplices:
		delaunay_edges.add((simplex[0], simplex[1]))
		delaunay_edges.add((simplex[1], simplex[2]))
		delaunay_edges.add((simplex[0], simplex[2]))

	# Calculate additional edges not in the MST
	additional_edges = delaunay_edges - set(mst.edges)
	extra_edges = random.sample(additional_edges, k=int(len(additional_edges) * percentage))
	mst.add_edges_from(extra_edges)

def get_room_center(room):
	return (room.x + room.width // 2, room.y + room.height // 2)

def connect_rooms_with_corridor(dungeon_layout, room1, room2):
	x1, y1 = get_room_center(room1)
	x2, y2 = get_room_center(room2)

	# Horizontal corridor
	for x in range(min(x1, x2), max(x1, x2) + 1):
		for i in range(0, CORRIDOR_WIDTH):
			dungeon_layout[y1 + i][x] = ' '

	# Vertical corridor
	for y in range(min(y1, y2), max(y1, y2) + 1):
		for i in range(0, CORRIDOR_WIDTH):
			dungeon_layout[y][x2 + i] = ' '

def build_corridors_from_mst(mst, dungeon_layout, rooms):
	for edge in mst.edges():
		room1 = rooms[edge[0]]
		room2 = rooms[edge[1]]
		connect_rooms_with_corridor(dungeon_layout, room1, room2)

class Cell:
	def __init__(self, x, y, width, height):
		self.rect = pygame.Rect(x, y, width, height)

def generate_cells(number_of_cells, map_width, map_height, buffer=SAFETY_MARGIN):
	cells = []
	for _ in range(number_of_cells):
		width = int(np.random.normal(loc=10, scale=3))
		height = int(np.random.normal(loc=10, scale=3))
		# Ensure cells are within bounds considering their dimensions
		x = np.random.randint(buffer, map_width - width - buffer)
		y = np.random.randint(buffer, map_height - height - buffer)
		cells.append(Cell(x, y, width, height))
	return cells

def separate_cells(cells, max_iterations=10000):
	moved = True
	iteration_count = 0

	while moved and iteration_count < max_iterations:
		moved = False
		for i, cell_a in enumerate(cells):
			for cell_b in cells[i+1:]:
				if cell_a.rect.colliderect(cell_b.rect):
					moved = True
					# Calculate overlap
					dx = min(cell_a.rect.right - cell_b.rect.left, cell_b.rect.right - cell_a.rect.left)
					dy = min(cell_a.rect.bottom - cell_b.rect.top, cell_b.rect.bottom - cell_a.rect.top)

					# Determine push direction
					if dx < dy:
						push_x = dx / 2
						cell_a.rect.x -= push_x
						cell_b.rect.x += push_x
					else:
						push_y = dy / 2
						cell_a.rect.y -= push_y
						cell_b.rect.y += push_y

		iteration_count += 1

	if iteration_count >= max_iterations:
		print("Warning: separate_cells reached maximum iterations")

def select_rooms(cells, min_size, map_width, map_height, buffer=SAFETY_MARGIN):
	return [Room(cell.rect.x, cell.rect.y, cell.rect.width, cell.rect.height)
			for cell in cells
			if cell.rect.width > min_size and cell.rect.height > min_size
			and cell.rect.right < map_width - buffer  # Adjusted
			and cell.rect.bottom < map_height - buffer]  # Adjusted


class Room:
	def __init__(self, x, y, width, height):
		# Initialize the room based on its top-left corner, width, and height
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		# Create a pygame.Rect object for the room
		self.rect = pygame.Rect(x, y, width, height)
		
	def create_room(self, dungeon_layout):
		for x in range(self.x, self.x + self.width):
			for y in range(self.y, self.y + self.height):
				# Check bounds before accessing the dungeon layout
				if 0 <= x < len(dungeon_layout[0]) and 0 <= y < len(dungeon_layout):
					if dungeon_layout[y][x] != ' ':  # Avoid overwriting corridors
						dungeon_layout[y][x] = ' '

class Level:
	enemy_types = ['S', 'W', 'K', 'B']  # Different types of enemies
	
	def __init__(self):

		# get the display surface 
		self.display_surface = pygame.display.get_surface()

		# Initialize the dungeon map as an instance attribute
		self.dungeon_layout = [['x' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

		# Initialize object, enemy, and player layout
		self.object_layout = [[' ' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

		# sprite group setup
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()
		
		# Load tilesheets
		Tile.load_tilesheet('wall', 'graphics/_Crypt/Tilesets/wall-1.png')
		Tile.load_tilesheet('floor', 'graphics/_Crypt/Tilesets/ground 1 to 2.png')
		Tile.load_tilesheet('overlay', 'graphics/_Crypt/Tilesets/wall-1.png')
		Tile.load_tilesheet('corner', 'graphics/_Crypt/Tilesets/wall-1.png')
		Tile.load_tilesheet('doors', 'graphics/_Crypt/Props/animated/doors/doors-metal-door frame 1-opening.png')

		# list of rooms
		self.rooms = []
  
		self.starting_room = None

		# attack sprites
		self.current_attack = None
		self.attack_sprites = pygame.sprite.Group()
		self.attackable_sprites = pygame.sprite.Group()

		# graph of rooms
		self.room_graph = {}

		# initialize player
		self.player = None
  
		# for debug in main
		self.enemy_sprites = pygame.sprite.Group()
  
  		# sprite setup
		self.create_map()
  
		# UI
		self.ui = UI()

	def calculate_distance(self, room1, room2):
		# Calculate the center points of both rooms
		center1 = (room1.x + room1.width // 2, room1.y + room1.height // 2)
		center2 = (room2.x + room2.width // 2, room2.y + room2.height // 2)
		# Use Euclidean distance to calculate the distance between the two centers
		distance = ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
		return distance

	def connect_to_closest_room(self, new_room):
		closest_room = None
		distance_to_closest = float('inf')
		for room in self.rooms:
			if room == new_room:  # Skip if it's the same room
				continue
			distance = self.calculate_distance(new_room, room)
			if distance < distance_to_closest:
				distance_to_closest = distance
				closest_room = room
		if closest_room:
			self.connect_rooms(new_room, closest_room, self.corridor_width)
			print('Room at '+ str(new_room.x), str(new_room.y) + ' connected to room at ' + str(closest_room.x), str(closest_room.y))

		else:
			print(f"No other room found to connect with room at ({new_room.x}, {new_room.y})")
	
	def get_tile_type(self, dungeon_layout, row_index, col_index):
		current_tile = dungeon_layout[row_index][col_index]
		below_tile = dungeon_layout[row_index + 1][col_index] if row_index + 1 < len(dungeon_layout) else None
		above_tile = dungeon_layout[row_index - 1][col_index] if row_index + 1 < len(dungeon_layout) else None
		left_tile = dungeon_layout[row_index][col_index - 1] if col_index + 1 < len(dungeon_layout) else None
		right_tile = dungeon_layout[row_index][col_index + 1] if col_index + 1 < len(dungeon_layout) else None
		two_below = dungeon_layout[row_index + 2][col_index] if row_index + 2 < len(dungeon_layout) else None
  
		if current_tile == 'x':
			if below_tile == 'x' and two_below == ' ':
				# Return coordinates for the specific wall tile at vertical transition
				return 'wall', (random.randint(0, 5), 9), None
			elif below_tile == ' ' and not two_below == 'x':
				return 'wall', (random.randint(0,5), 10), 'bottom'
			elif right_tile == ' ' and left_tile == 'x' and above_tile == 'x' and below_tile == ' ': # bottom right corner
				print('right corner made')
				return 'wall', (3, 4), None
			elif above_tile == ' ':
				return 'wall', (2, 1), 'top'
			else:
				# Return coordinates for a regular wall tile
				return 'wall', (2, 1), None
		elif current_tile == ' ':
			# Return coordinates for a floor tile
			return 'floor', (random.randint(1,3), random.randint(1,2)), None

		return None, None, None  # Default case if no match is found
	
	def get_overlay_tile(self, dungeon_layout, row_index, col_index):
		# Determine if an overlay tile should be placed here
		current_tile = dungeon_layout[row_index][col_index]
		below_tile = dungeon_layout[row_index + 1][col_index] if row_index + 1 < len(dungeon_layout) else None
		above_tile = dungeon_layout[row_index - 1][col_index] if row_index - 1 >= 0 else None
		left_tile = dungeon_layout[row_index][col_index - 1] if col_index - 1 >= 0 else None
		right_tile = dungeon_layout[row_index][col_index + 1] if col_index + 1 < len(dungeon_layout[row_index]) else None
		up_right = dungeon_layout[row_index - 1][col_index + 1] if row_index + 1 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout) else None
		down_left = dungeon_layout[row_index + 1][col_index - 1] if row_index + 1 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout) else None
		down_right = dungeon_layout[row_index + 1][col_index + 1] if row_index + 1 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout[0]) else None


		if current_tile == ' ' and below_tile == 'x':
			# Return tile_type, coordinates, edge type, and is_obstacle flag
			return 'overlay', (2, 0), 'top', True
		elif current_tile == ' ' and above_tile == 'x':
			return 'overlay', (2, 6), 'bottom', True
		elif current_tile == ' ' and right_tile == 'x':
			return 'overlay', (0,2), 'bottom', True
		elif current_tile == ' ' and left_tile == 'x':
			return 'overlay', (4, 2), 'bottom', True

		return None

	def get_corner_tile(self, dungeon_layout, row_index, col_index):
		# Determine if an overlay tile should be placed here
		current_tile = dungeon_layout[row_index][col_index]
		below_tile = dungeon_layout[row_index + 1][col_index] if row_index + 1 < len(dungeon_layout) else None
		above_tile = dungeon_layout[row_index - 1][col_index] if row_index - 1 >= 0 else None
		left_tile = dungeon_layout[row_index][col_index - 1] if col_index - 1 >= 0 else None
		right_tile = dungeon_layout[row_index][col_index + 1] if col_index + 1 < len(dungeon_layout[row_index]) else None
		up_right = dungeon_layout[row_index - 1][col_index + 1] if row_index + 1 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout) else None
		up_left = dungeon_layout[row_index - 1][col_index - 1] if row_index + 1 < len(dungeon_layout) and col_index - 1 < len(dungeon_layout) else None
		down_left = dungeon_layout[row_index + 1][col_index - 1] if row_index + 1 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout) else None
		down_right = dungeon_layout[row_index + 1][col_index + 1] if row_index + 1 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout[0]) else None
		two_down_right = dungeon_layout[row_index + 2][col_index + 1] if row_index + 2 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout[0]) else None
		two_down_left = dungeon_layout[row_index + 2][col_index - 1] if row_index + 2 < len(dungeon_layout) and col_index - 1 < len(dungeon_layout[0]) else None
		two_down = dungeon_layout[row_index + 2][col_index] if row_index + 2 < len(dungeon_layout) else None		
  
		#floor on top
		if current_tile == ' ' and below_tile == ' ' and right_tile == ' ' and left_tile == ' ' and down_left == 'x':
			return 'corner', (4, 1), 'top', True
		elif current_tile == ' ' and below_tile == ' ' and right_tile == ' ' and left_tile == ' ' and down_right == 'x':
			return 'corner', (0, 1), 'top', True
		
		# floor on left and bottom, wall on right
		elif current_tile == ' ' and above_tile == ' ' and right_tile == ' ' and left_tile == ' ' and up_right == 'x':
			return 'corner', (0, 5), 'bottom', True
		elif current_tile == ' ' and above_tile == ' ' and right_tile == 'x' and down_right == ' ':
			return 'corner', (0, 4), 'bottom', True
		elif current_tile == ' ' and above_tile == ' ' and right_tile == 'x' and down_right == 'x' and two_down_right == ' ':
			return 'corner', (0, 3), 'bottom', True
		elif current_tile == ' ' and below_tile == ' ' and right_tile == 'x' and left_tile == ' ' and down_left == ' ' and above_tile == 'x':
			return 'corner', (0, 2), 'top', True
		elif current_tile == 'x' and below_tile == ' ' and right_tile == 'x' and left_tile == 'x' and down_right == 'x' and above_tile == 'x' and down_left == ' ':
			return 'corner', (0, 2), 'top', True
		elif current_tile == 'x' and below_tile == 'x' and right_tile == 'x' and left_tile == 'x' and down_right == 'x' and above_tile == 'x' and down_left == 'x' and two_down == ' ' and two_down_left == ' ' and two_down_right == 'x':
			return 'corner', (1, 3), 'top', True

		# floor on right and bottom, wall on left
		elif current_tile == ' ' and above_tile == ' ' and right_tile == ' ' and left_tile == ' ' and up_left == 'x':
			return 'corner', (4, 5), 'bottom', True
		elif current_tile == ' ' and above_tile == ' ' and left_tile == 'x' and down_left == ' ':
			return 'corner', (4, 4), 'bottom', True
		elif current_tile == ' ' and above_tile == 'x' and left_tile == 'x' and down_left == ' ':
			return 'corner', (4, 4), 'bottom', True

		elif current_tile == ' ' and above_tile == ' ' and left_tile == 'x' and down_left == 'x' and two_down_left == ' ':
			return 'corner', (4, 3), 'bottom', True
		elif current_tile == ' ' and below_tile == ' ' and right_tile == ' ' and left_tile == 'x' and down_right == ' ' and above_tile == 'x':
			return 'corner', (4, 2), 'top', True
		elif current_tile == 'x' and below_tile == ' ' and left_tile == 'x' and right_tile == 'x' and down_left == 'x' and above_tile == 'x' and down_right == ' ':
			return 'corner', (4, 2), 'top', True
		elif current_tile == 'x' and below_tile == 'x' and left_tile == 'x' and right_tile == 'x' and down_left == 'x' and above_tile == 'x' and down_right == 'x' and two_down == ' ' and two_down_right == ' ' and two_down_left == 'x':
			return 'corner', (3, 3), 'top', True

		# floor on top and left or right
		if current_tile == ' ' and below_tile == 'x' and right_tile == ' ' and left_tile == 'x' and down_left == 'x':
			return 'corner', (3, 1), 'top', True
		if current_tile == ' ' and below_tile == 'x' and right_tile == 'x' and left_tile == ' ' and down_right == 'x':
			return 'corner', (1, 1), 'top', True

		return None
 
	def populate_objects(self):
		enemy_types = self.enemy_types
		for room in self.rooms:
			if room == self.starting_room:
				continue
			# Place an item in the center of each room
			center_x, center_y = room.x + room.width // 2, room.y + room.height // 2
			if self.dungeon_layout[center_y][center_x] == ' ':
				self.object_layout[center_y][center_x] = 'I'  # 'I' for Item

			# Place enemies randomly in rooms
			for _ in range(random.randint(1, 2)):  # Random number of enemies
				placed = False
				attempts = 0
				while not placed and attempts < 3:
					attempts += 1
					enemy_x, enemy_y = random.randint(room.x + 2, room.x + room.width - 4), random.randint(room.y + 2, room.y + room.height - 4)
					if self.dungeon_layout[enemy_y][enemy_x] == ' ':
						enemy_type = random.choice(enemy_types)  # Randomly choose an enemy type
						self.object_layout[enemy_y][enemy_x] = enemy_type  # Place enemy type on Map2
						placed = True

	def create_map(self):
		print("Starting map creation")
		self.generate_procedural_map()
		self.place_tiles_and_enemies()
		self.fix_border_and_walls(self.dungeon_layout)
		self.place_doors()
		
		print('Map and objects generated')
		for row in self.dungeon_layout:
			print(''.join(row))

	def place_doors(self):
		# Additional code for door creation
		for room in self.rooms:
			central_x = room.x + room.width // 2
			door_bottom_row_y = room.y + 1

			door_x = central_x - 2  # Center the door

			# Ensure there's enough space above the wall and the top wall is suitable
			if door_bottom_row_y - 3 >= 0:
				# Check if the bottom row of the door and two rows above it are suitable
				bottom_row_ok = all(self.dungeon_layout[door_bottom_row_y][max(0, door_x + i)] == ' ' for i in range(4))
				one_row_above_ok = all(self.dungeon_layout[door_bottom_row_y - 1][max(0, door_x + i)] == ' ' for i in range(4))
				two_rows_above_ok = all(self.dungeon_layout[door_bottom_row_y - 2][max(0, door_x + i)] == 'x' for i in range(4))
				three_rows_above_ok = all(self.dungeon_layout[door_bottom_row_y - 3][max(0, door_x + i)] == 'x' for i in range(4))
				four_rows_above_ok = all(self.dungeon_layout[door_bottom_row_y - 4][max(0, door_x + i)] == 'x' for i in range(4))

				if bottom_row_ok and one_row_above_ok and two_rows_above_ok and three_rows_above_ok and four_rows_above_ok:
					self.create_door(door_x * TILESIZE, (door_bottom_row_y - 3) * TILESIZE)

	def place_tiles_and_enemies(self):
		player_created = False
		for row_index, row in enumerate(self.dungeon_layout):
			for col_index, cell in enumerate(row):
				self.place_tile(row_index, col_index)
				self.try_place_player(cell, row_index, col_index, player_created)
		self.place_enemies()

	def place_tile(self, row_index, col_index):
		x, y = col_index * TILESIZE, row_index * TILESIZE
		tile_type, tile_coords, edge_type = self.get_tile_type(self.dungeon_layout, row_index, col_index)
		if tile_type:
			obstacle_group = self.obstacle_sprites if tile_type in ['wall', 'overlay', 'corner'] else None
			Tile((x, y), self.visible_sprites, obstacle_group, tile_type, tile_coords, tile_type, edge_type)
			self.try_place_overlay_or_corner_tile(row_index, col_index)

	def try_place_overlay_or_corner_tile(self, row_index, col_index):
		overlay_tile = self.get_overlay_tile(self.dungeon_layout, row_index, col_index)
		if overlay_tile:
			tile_type, tile_coords, edge_type, is_obstacle = overlay_tile
			obstacle_group = self.obstacle_sprites if is_obstacle else None
			Tile((col_index * TILESIZE, row_index * TILESIZE), self.visible_sprites, obstacle_group, tile_type, tile_coords, tile_type, edge_type)
		corner_tile = self.get_corner_tile(self.dungeon_layout, row_index, col_index)
		if corner_tile:
			tile_type, tile_coords, edge_type, is_obstacle = corner_tile
			obstacle_group = self.obstacle_sprites if is_obstacle else None
			Tile((col_index * TILESIZE, row_index * TILESIZE), self.visible_sprites, obstacle_group, tile_type, tile_coords, tile_type, edge_type)

	def try_place_player(self, cell, row_index, col_index, player_created_flag):
		x, y = col_index * TILESIZE, row_index * TILESIZE
		if cell == 'p' and not player_created_flag:
			self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites, self.create_attack, self.destroy_attack, self.create_magic)
			player_created_flag = True
		if self.player is None:
			print("Player was not created!")

	def place_enemies(self):
		for room in self.rooms:
			# Calculate inner area bounds to place enemies
			start_x = max(room.x + 3, 3)
			end_x = min(room.x + room.width - 3, MAP_WIDTH - 3)
			start_y = max(room.y + 3, 3)
			end_y = min(room.y + room.height - 3, MAP_HEIGHT - 3)

			# Place enemies randomly in rooms, ensuring they are away from walls
			for _ in range(random.randint(1, 2)):  # Random number of enemies
				placed = False
				attempts = 0
				while not placed and attempts < 10 and room != self.starting_room:
					attempts += 1
					enemy_x = random.randint(start_x, end_x)
					enemy_y = random.randint(start_y, end_y)

					if self.is_valid_enemy_position(enemy_x, enemy_y):
						enemy_type = random.choice(self.enemy_types)  # Randomly choose an enemy type
						self.create_enemy(enemy_type, enemy_x, enemy_y)
						placed = True

	def is_valid_enemy_position(self, x, y):
		# Check if the position is suitable for placing an enemy
		for i in range(-3, 4):  # Check in a 7x7 grid centered on the position
			for j in range(-3, 4):
				if self.dungeon_layout[y + j][x + i] != ' ':
					return False
		return True

	def create_enemy(self, enemy_type, col_index, row_index):
		x, y = col_index * TILESIZE, row_index * TILESIZE
		enemy_name = {
			'S': 'Spider/1',
			'W': 'Worm/1',
			'K': 'Skeleton/1',
			'B': 'Worm/2'
		}.get(enemy_type)
		if enemy_name:
			Enemy(enemy_name, (x, y), [self.visible_sprites, self.attackable_sprites, self.enemy_sprites], self.obstacle_sprites)
			print(f'{enemy_name} enemy rendered at position:', x, y)

	def create_door(self, x, y):
		door_width, door_height = 4, 4
		for i in range(door_width):
			for j in range(door_height):
				door_tile_x = (x // TILESIZE) + i
				door_tile_y = (y // TILESIZE) + j

				if j == 3:  # Mark the bottom row of the door
					self.dungeon_layout[door_tile_y][door_tile_x] = 'D'

				tile_coords = (i, j)
				door_pos = (x + i * TILESIZE, y + j * TILESIZE)
				Tile(door_pos, self.visible_sprites, None, 'doors', tile_coords, 'door')

	def create_attack(self):
		self.current_attack = Weapon(self.player, [self.visible_sprites, self.attack_sprites])
		
	def destroy_attack(self):
		if self.current_attack:
			self.current_attack.kill()
		self.current_attack = None
	
	def player_attack_logic(self):
		if self.attack_sprites:
			for attack_sprite in self.attack_sprites:
				collision_sprites = pygame.sprite.spritecollide(attack_sprite, self.attackable_sprites, False)
				for target_sprite in collision_sprites:
					if target_sprite.sprite_type == 'enemy' and target_sprite.status != 'final_death':
						target_sprite.get_damage(self.player, attack_sprite.sprite_type)

	def create_magic(self, style, strength, cost):
		print(style)
		print(strength)
		print(cost)

	def find_valid_player_position(self, room):
		# Calculate the center of the room
		center_x = room.x + room.width // 2
		center_y = room.y + room.height // 2

		# Ensure the center is not out of bounds
		center_x = max(min(center_x, MAP_WIDTH - 1), 0)
		center_y = max(min(center_y, MAP_HEIGHT - 1), 0)

		# Check if the center is a wall tile; if so, find the nearest floor tile
		if self.dungeon_layout[center_y][center_x] == 'x':
			for y in range(room.y + 1, room.y + room.height - 1):
				for x in range(room.x + 1, room.x + room.width - 1):
					if self.dungeon_layout[y][x] == ' ':
						return x, y
		else:
			return center_x, center_y

		return None, None  # Return None if no valid position is found

	def generate_procedural_map(self):
		# Generate and separate cells
		cells = generate_cells(25, MAP_WIDTH, MAP_HEIGHT)
		separate_cells(cells)

		# Convert cells to rooms and add to self.rooms
		self.rooms = select_rooms(cells, min_size=8, map_width=MAP_WIDTH, map_height=MAP_HEIGHT)

		# Fill rooms in the dungeon layout
		for room in self.rooms:
			print(f'Room rendered at position:', room.x, room.y)
			room.create_room(self.dungeon_layout)
			
		# Step 3: Construct MST and corridors
		delaunay_tri = create_delaunay_triangulation(self.rooms)
		mst = create_mst(delaunay_tri)
		add_extra_edges_to_mst(mst, delaunay_tri, percentage=0.15)  # Adjust percentage as needed
		build_corridors_from_mst(mst, self.dungeon_layout, self.rooms)

		# Place the player in the first room
		first_room = self.rooms[0]  # Select the first room
		self.starting_room = first_room
		player_x, player_y = self.find_valid_player_position(first_room)
		if player_x is not None and player_y is not None:
			self.player = Player((player_x * TILESIZE, player_y * TILESIZE), [self.visible_sprites], self.obstacle_sprites, self.create_attack, self.destroy_attack, self.create_magic)
		else:
			print("Failed to place the player in a valid position")

		# Populate the dungeon with objects
		self.populate_objects()
  
		# Fix single-tile-thick walls
		self.fix_border_and_walls(self.dungeon_layout)

		print('Map and objects generated')
	
	def add_room(self, room, corridor_width):
		# Adjusted to consider buffer margin
		overlap = False
		buffer = SAFETY_MARGIN  # Define buffer margin
		corridor_and_wall_space = corridor_width + 1

		for r in self.rooms:
			if (room.x < r.x + r.width + corridor_and_wall_space and
				room.x + room.width + corridor_and_wall_space > r.x and
				room.y < r.y + r.height + corridor_and_wall_space and
				room.y + room.height + corridor_and_wall_space > r.y):
				overlap = True
				break

		# Check if room is too close to the edges considering buffer
		too_close_to_edge = (room.x < buffer or 
							room.y < buffer or 
							room.x + room.width + corridor_width > MAP_WIDTH - buffer or 
							room.y + room.height + corridor_width > MAP_HEIGHT - buffer)
		
		if not overlap and not too_close_to_edge:
			room.create_room(self.dungeon_layout)
			self.rooms.append(room)
			return True
		else:
			print("Room is either overlapping with another room or too close to the edge.")
			return False

	def connect_rooms(self, room1, room2, corridor_width):
		# Find center of rooms
		x1, y1 = room1.x + room1.width // 2, room1.y + room1.height // 2
		x2, y2 = room2.x + room2.width // 2, room2.y + room2.height // 2

		half_width = 3

		# Horizontal then vertical or vertical then horizontal
		if random.choice([True, False]):
			# Horizontal then vertical
			for x in range(min(x1, x2), max(x1, x2) + 1):
				for w in range(-half_width, half_width + 1):
					if self.is_corridor_space(x, y1 + w, room1, room2, include_room_edge=True):
						self.dungeon_layout[y1 + w][x] = ' '
			for y in range(min(y1, y2), max(y1, y2) + 1):
				for w in range(-half_width, half_width + 1):
					if self.is_corridor_space(x2 + w, y, room1, room2, include_room_edge=True):
						self.dungeon_layout[y][x2 + w] = ' '
		else:
			# Vertical then horizontal
			for y in range(min(y1, y2), max(y1, y2) + 1):
				for w in range(-half_width, half_width + 1):
					if self.is_corridor_space(x1 + w, y, room1, room2, include_room_edge=True):
						self.dungeon_layout[y][x1 + w] = ' '
			for x in range(min(x1, x2), max(x1, x2) + 1):
				for w in range(-half_width, half_width + 1):
					if self.is_corridor_space(x, y2 + w, room1, room2, include_room_edge=True):
						self.dungeon_layout[y2 + w][x] = ' '

	def is_corridor_space(self, x, y, room1, room2, include_room_edge=False):
		"""
		Check if the given x, y position is a valid space for a corridor segment.
		It should not be within the walls of the rooms it is connecting, unless
		it's at the edge of the room for merging purposes.
		"""
		in_room1 = (x >= room1.x + 1 and x < room1.x + room1.width + 1 and y >= room1.y + 1 and y < room1.y + room1.height + 1 )
		in_room2 = (x >= room2.x + 1 and x < room2.x + room2.width + 1 and y >= room2.y + 1 and y < room2.y + room2.height + 1 )

		if include_room_edge:
			return not (in_room1 and in_room2)
		else:
			return not (in_room1 or in_room2)

	def fix_border_and_walls(self, dungeon_layout):
		height = MAP_HEIGHT
		width = MAP_WIDTH
		border_thickness = 3  # Number of tiles for the border

		# Add a border of 'x' tiles around the map
		for y in range(height):
			for x in range(width):
				if y < border_thickness or y >= height - border_thickness or \
				x < border_thickness or x >= width - border_thickness:
					dungeon_layout[y][x] = 'x'

		# Fix single-tile-thick walls inside the map, skipping the border area
		for y in range(border_thickness, height - border_thickness):
			for x in range(border_thickness, width - border_thickness):
				if dungeon_layout[y][x] == 'x':
					# Check adjacent tiles
					left = dungeon_layout[y][x - 1]
					right = dungeon_layout[y][x + 1]
					up = dungeon_layout[y - 1][x]
					down = dungeon_layout[y + 1][x]

					# Convert to ' ' if surrounded by ' ' on opposite sides
					if (left == ' ' and right == ' ') or (up == ' ' and down == ' '):
						dungeon_layout[y][x] = ' '

	def run(self):
		# update and draw the game
		if self.player is None:
			raise ValueError("Player object has not been initialized before running the level.")
		
		self.visible_sprites.custom_draw(self.player)

		self.player_attack_logic()
  
		self.visible_sprites.enemy_update(self.player)
		
		self.visible_sprites.update()
		

class YSortCameraGroup(pygame.sprite.Group):
	def __init__(self):

		# general setup 
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.half_width = self.display_surface.get_size()[0] // 2
		self.half_height = self.display_surface.get_size()[1] // 2
		self.offset = pygame.math.Vector2()

	def custom_draw(self,player):

		# getting the offset 
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height
  
		# Draw all non-player and non-top-edge wall tiles
		for sprite in self.sprites():
			if sprite != player and not (hasattr(sprite, 'edge_type') and sprite.edge_type == 'top'):
				offset_pos = sprite.rect.topleft - self.offset
				self.display_surface.blit(sprite.image, offset_pos)
				# Draw the hitbox for enemy sprites with offset
				if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'enemy':
					hitbox_pos = sprite.hitbox.topleft - self.offset
					sprite.draw_hitbox(self.display_surface, hitbox_pos)

		# Draw player
		offset_pos = player.rect.topleft - self.offset
		self.display_surface.blit(player.image, offset_pos)

		# Draw top-edge wall tiles last
		for sprite in self.sprites():
			if hasattr(sprite, 'edge_type') and sprite.edge_type == 'top':
				offset_pos = sprite.rect.topleft - self.offset
				self.display_surface.blit(sprite.image, offset_pos)

	def enemy_update(self, player):
		enemy_sprites = [sprite for sprite in self.sprites() if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'enemy']
		for enemy in enemy_sprites:
			
			enemy.enemy_update(player)
		