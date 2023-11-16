
import pygame 
from settings import *
from tile import Tile
from player import Player
from debug import debug
import random
from weapon import Weapon
from ui import UI

class Room:
	def __init__(self, x, y, width, height):
		# Initialize the room based on its top-left corner, width, and height
		self.x = x
		self.y = y
		self.width = width
		self.height = height

	def create_room(self, dungeon_layout):
		# Fill the defined area of the dungeon map with open space
		for x in range(self.x, self.x + self.width):
			for y in range(self.y, self.y + self.height):
	   			if dungeon_layout[y][x] != ' ':  # Avoid overwriting corridors
		   				dungeon_layout[y][x] = ' '


class Level:
	corridor_width = 4
	
	def __init__(self):

		# get the display surface 
		self.display_surface = pygame.display.get_surface()

		# Initialize the dungeon map as an instance attribute
		self.dungeon_layout = [['x' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

		# sprite group setup
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()
		
		# Load tilesheets
		Tile.load_tilesheet('wall', 'graphics/_Crypt/Tilesets/wall-1.png')
		Tile.load_tilesheet('floor', 'graphics/_Crypt/Tilesets/ground 1 to 2.png')
		Tile.load_tilesheet('overlay', 'graphics/_Crypt/Tilesets/wall-1.png')
  
		# list of rooms
		self.rooms = []

		# attack sprites
		self.current_attack = None
  
		# graph of rooms
		self.room_graph = {}
  
		# initialize player
		self.player = None
  
  		# sprite setup
		self.create_map()
  
		# UI
		self.ui = UI()

	def add_room_to_graph(self, room):
		self.room_graph[room] = []
	
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
			self.room_graph[new_room].append(closest_room)
			self.room_graph[closest_room].append(new_room)
		else:
			print(f"No other room found to connect with room at ({new_room.x}, {new_room.y})")

	def ensure_all_rooms_connected(self):
		visited = set()
		self.dfs(self.rooms[0], visited)  # Start DFS from the first room
		for room in self.rooms:
			if room not in visited:
				self.connect_to_closest_room(room)
				self.dfs(room, visited)
		
		# Debugging: Print the room graph to ensure all rooms are connected
		for room, connections in self.room_graph.items():
			print(f"Room at ({room.x}, {room.y}) is connected to {[f'({r.x}, {r.y})' for r in connections]}")

	def dfs(self, room, visited):
		visited.add(room)
		for connected_room in self.room_graph[room]:
			if connected_room not in visited:
				self.dfs(connected_room, visited)
	
	def get_tile_type(self, dungeon_layout, row_index, col_index):
		current_tile = dungeon_layout[row_index][col_index]
		below_tile = dungeon_layout[row_index + 1][col_index] if row_index + 1 < len(dungeon_layout) else None
		above_tile = dungeon_layout[row_index - 1][col_index] if row_index + 1 < len(dungeon_layout) else None
		left_tile = dungeon_layout[row_index][col_index - 1] if col_index + 1 < len(dungeon_layout) else None
		right_tile = dungeon_layout[row_index][col_index + 1] if col_index + 1 < len(dungeon_layout) else None
		two_below = dungeon_layout[row_index + 2][col_index] if row_index + 2 < len(dungeon_layout) else None
		two_above = dungeon_layout[row_index - 2][col_index] if row_index + 2 < len(dungeon_layout) else None
		three_below = dungeon_layout[row_index + 3][col_index] if row_index + 3 < len(dungeon_layout) else None
		up_right = dungeon_layout[row_index + 1][col_index + 1] if row_index + 1 < len(dungeon_layout) and col_index + 1 < len(dungeon_layout) else None
  
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
			return 'floor', (0, 1), None
		# Add more conditions as needed for other types of tiles

		return None, None, None  # Default case if no match is found
	
	def get_overlay_tile(self, dungeon_layout, row_index, col_index):
		# Determine if an overlay tile should be placed here
		current_tile = dungeon_layout[row_index][col_index]
		below_tile = dungeon_layout[row_index + 1][col_index] if row_index + 1 < len(dungeon_layout) else None

		if current_tile == ' ' and below_tile == 'x':
			# Return tile_type, coordinates, edge type, and is_obstacle flag
			return 'overlay', (2, 0), 'top', True
		return None



	def get_corner_tile(self, dungeon_layout, x, y):
		# Determine if a corner tile should be placed here
		# Return the tile type and coordinates if a corner tile is needed, else None
		pass  # Implement the logic here
	
	def create_map(self):
		# Procedural map generation
		self.generate_procedural_map()
		player_created = False
		for row_index, row in enumerate(self.dungeon_layout):
			for col_index, col in enumerate(row):
				x = col_index * TILESIZE
				y = row_index * TILESIZE

				# Handle base tile
				tile_type, tile_coords, edge_type = self.get_tile_type(self.dungeon_layout, row_index, col_index)
				if tile_type:
					obstacle_group = self.obstacle_sprites if tile_type == 'wall' or tile_type == 'overlay' else None
					Tile((x, y), self.visible_sprites, obstacle_group, tile_type, tile_coords, tile_type, edge_type)

				# Handle overlay tile
				overlay_tile = self.get_overlay_tile(self.dungeon_layout, row_index, col_index)
				if overlay_tile:
					tile_type, tile_coords, edge_type, is_obstacle = overlay_tile
					obstacle_group = self.obstacle_sprites if is_obstacle else None
					Tile((x, y), self.visible_sprites, obstacle_group, tile_type, tile_coords, tile_type, edge_type)
				'''if corner_tile:
					# Make sure corner_tile contains all the required arguments for Tile constructor
					Tile((x, y), self.visible_sprites, None, *corner_tile)'''

				# Player creation logic
				if col == 'p' and not player_created:
					self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites, self.create_attack, self.destroy_attack)
					player_created = True

		if self.player is None:
			print("Player was not created!")
		else:
			print(f"Player object: {self.player}")


	def create_attack(self):
		self.current_attack = Weapon(self.player, [self.visible_sprites])
		
	def destroy_attack(self):
		if self.current_attack:
			self.current_attack.kill()
		self.current_attack = None
	
	def find_valid_player_position(self, room):
		# Adjust the start and end positions of the loop to ensure it's within room boundaries and dungeon layout
		start_x = max(room.x + 1, 1)  # Ensure it's greater than 0
		end_x = min(room.x + room.width - 1, MAP_WIDTH - 1)  # Ensure it's less than MAP_WIDTH
		start_y = max(room.y + 1, 1)  # Ensure it's greater than 0
		end_y = min(room.y + room.height - 1, MAP_HEIGHT - 1)  # Ensure it's less than MAP_HEIGHT

		spawn_x = (end_x + start_x) // 2
		spawn_y = (end_y + start_y) // 2
		
		return spawn_x, spawn_y
  
		'''for y in range(start_y, end_y):
			for x in range(start_x, end_x):
				# Check if the tile is open space and not at the edge
				if self.dungeon_layout[y][x] == ' ':
					return x, y

		return None, None  # Return None if no valid position is found'''

	def generate_procedural_map(self):
		# Always create the first room and place the player inside it
		first_room = Room(random.randint(1, MAP_WIDTH - 1), random.randint(1, MAP_HEIGHT - 1), random.randint(10, 20), random.randint(10, 20))
		self.add_room(first_room, self.corridor_width)
		self.add_room_to_graph(first_room)  # Add the first room to the graph

		# Find a valid open position within the first room for the player
		player_x, player_y = self.find_valid_player_position(first_room)
		if player_x is not None and player_y is not None:
			self.player = Player((player_x * TILESIZE, player_y * TILESIZE), [self.visible_sprites], self.obstacle_sprites, self.create_attack, self.destroy_attack)
			print(f"Player created at: {(player_x, player_y)}")
		else:
			print("Failed to place the player in a valid position")

		# Generate additional rooms and connect them
		for i in range(1, 25):  # Start from 1 since the first room is already created
			room = Room(random.randint(1, MAP_WIDTH - 10), random.randint(1, MAP_HEIGHT - 10), random.randint(8, 20), random.randint(8, 20))
			if self.add_room(room, self.corridor_width):
				self.add_room_to_graph(room)  # Add the room to the graph
				self.connect_to_closest_room(room)  # Connect the room to the closest one
		for row in self.dungeon_layout:
			print(''.join(row))
		# Ensure all rooms are connected
		self.ensure_all_rooms_connected()

		print('map generated')

	def add_room(self, room, corridor_width):
		# Check if room overlaps with existing rooms or is too close to the edges.
		overlap = False

		corridor_and_wall_space = corridor_width + 1  # Add 1 for wall thickness
		for r in self.rooms:
			if (room.x < r.x + r.width + corridor_and_wall_space and
				room.x + room.width + corridor_and_wall_space > r.x and
				room.y < r.y + r.height + corridor_and_wall_space and
				room.y + room.height + corridor_and_wall_space > r.y):
				overlap = True
				break

		# Check if room is too close to the edges
		too_close_to_edge = (room.x < SAFETY_MARGIN or 
								room.y < SAFETY_MARGIN or 
								room.x + room.width > MAP_WIDTH - SAFETY_MARGIN or 
								room.y + room.height > MAP_HEIGHT - SAFETY_MARGIN)
		
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

		half_width = corridor_width // 2

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

	def run(self):
		# update and draw the game
		if self.player is None:
			raise ValueError("Player object has not been initialized before running the level.")
		
		self.visible_sprites.custom_draw(self.player)
		
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

		# Draw player
		offset_pos = player.rect.topleft - self.offset
		self.display_surface.blit(player.image, offset_pos)

		# Draw top-edge wall tiles last
		for sprite in self.sprites():
			if hasattr(sprite, 'edge_type') and sprite.edge_type == 'top':
				offset_pos = sprite.rect.topleft - self.offset
				self.display_surface.blit(sprite.image, offset_pos)

		