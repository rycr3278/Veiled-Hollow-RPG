
import pygame 
from settings import *
from tile import Tile
from player import Player
from debug import debug

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
                dungeon_layout[y][x] = ' '

class Level:
	def __init__(self):

		# get the display surface 
		self.display_surface = pygame.display.get_surface()

		# Initialize the dungeon map as an instance attribute
		self.dungeon_layout = [['x' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

		# sprite group setup
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()
		
		# list of rooms
		self.rooms = []

		# graph of rooms
		self.room_graph = {}
  
		# initialize player
		self.player = None
  
  		# sprite setup
		self.create_map()

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
			distance = self.calculate_distance(new_room, room)
			if distance < distance_to_closest:
				distance_to_closest = distance
				closest_room = room
		self.connect_rooms(new_room, closest_room)
		self.room_graph[new_room].append(closest_room)
		self.room_graph[closest_room].append(new_room)

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
	
 
	def create_map(self):
        # Procedural map generation
		self.generate_procedural_map()
		player_created = False
		for row_index, row in enumerate(self.dungeon_layout):
			for col_index, col in enumerate(row):
				x = col_index * TILESIZE
				y = row_index * TILESIZE
				if col == 'x':
					Tile((x, y), [self.visible_sprites, self.obstacle_sprites])
				elif col == 'p' and not player_created:
					self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites)
					print(f"Player created at: {(x, y)}")  # Debug print
					player_created = True

		if self.player is None:
			print("Player was not created!")  # Debug print
		else:
			print(f"Player object: {self.player}")  # Debug print

	def generate_procedural_map(self):
		# Always create the first room and place the player inside it
		first_room = Room(random.randint(1, MAP_WIDTH - 11), random.randint(1, MAP_HEIGHT - 11), random.randint(5, 10), random.randint(5, 10))
		self.add_room(first_room)
		self.add_room_to_graph(first_room)  # Add the first room to the graph
		player_x = first_room.x + first_room.width // 2
		player_y = first_room.y + first_room.height // 2
		self.dungeon_layout[player_y][player_x] = 'p'
		self.player = Player((player_x * TILESIZE, player_y * TILESIZE), [self.visible_sprites], self.obstacle_sprites)
		print(f"Player created at: {(player_x * TILESIZE, player_y * TILESIZE)}")

		# Generate additional rooms and connect them
		for i in range(1, 10):  # Start from 1 since the first room is already created
			room = Room(random.randint(1, MAP_WIDTH - 11), random.randint(1, MAP_HEIGHT - 11), random.randint(5, 10), random.randint(5, 10))
			if self.add_room(room):
				self.add_room_to_graph(room)  # Add the room to the graph
				self.connect_to_closest_room(room)  # Connect the room to the closest one
		for row in self.dungeon_layout:
			print(''.join(row))
		# Ensure all rooms are connected
		self.ensure_all_rooms_connected()
		
		print('map generated')


	def add_room(self, room):
		# Check if room overlaps with existing rooms or is too close to the edges.
		overlap = False
		for r in self.rooms:
			if (room.x < r.x + r.width and room.x + room.width > r.x and
				room.y < r.y + r.height and room.y + room.height > r.y):
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


	def connect_rooms(self, room1, room2):
		# Find center of rooms
		x1, y1 = room1.x + room1.width // 2, room1.y + room1.height // 2
		x2, y2 = room2.x + room2.width // 2, room2.y + room2.height // 2

		# Determine the order of connection (horizontal first or vertical first)
		# by random choice or some heuristic
		if random.choice([True, False]):
			# Horizontal then vertical
			for x in range(min(x1, x2), max(x1, x2) + 1):
				self.dungeon_layout[y1][x] = ' '
			for y in range(min(y1, y2), max(y1, y2) + 1):
				self.dungeon_layout[y][x2] = ' '
		else:
			# Vertical then horizontal
			for y in range(min(y1, y2), max(y1, y2) + 1):
				self.dungeon_layout[y][x1] = ' '
			for x in range(min(x1, x2), max(x1, x2) + 1):
				self.dungeon_layout[y2][x] = ' '



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
  
		# create ' '
		self.floor_surf = pygame.image.load('graphics/tilemap/ground.png').convert()
		self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

	def custom_draw(self,player):

		# getting the offset 
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height
  
		# draw ' '
		floor_offset_pos = self.floor_rect.topleft - self.offset
		self.display_surface.blit(self.floor_surf, floor_offset_pos)

		# for sprite in self.sprites():
		for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image,offset_pos)