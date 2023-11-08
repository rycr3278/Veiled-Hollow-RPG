
import pygame 
from settings import *
from tile import Tile
from player import Player
from debug import debug

class Level:
	def __init__(self):

		# get the display surface 
		self.display_surface = pygame.display.get_surface()

		# sprite group setup
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()

		# sprite setup
		self.create_map()

	def create_map(self):
        # Procedural map generation
		self.dungeon_layout = self.generate_procedural_map()
		for row_index, row in enumerate(self.dungeon_layout):
			for col_index, col in enumerate(row):
				x = col_index * TILESIZE
				y = row_index * TILESIZE
				if col == 'x':
					Tile((x, y), [self.visible_sprites, self.obstacle_sprites])
				elif col == 'p':
					self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites)

	def generate_procedural_map(self):
        # Define the size of the map
		map_width = 50
		map_height = 50
  
		# Create an empty map
		dungeon_map = [[' ' for _ in range(map_width)] for _ in range(map_height)]

		# Fill the border with 'x' tiles
		for x in range(map_width):
			dungeon_map[0][x] = 'x'  # Top border
			dungeon_map[map_height - 1][x] = 'x'  # Bottom border
		for y in range(map_height):
			dungeon_map[y][0] = 'x'  # Left border
			dungeon_map[y][map_width - 1] = 'x'  # Right border


		# Random walk parameters
		directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Up, down, left, right
		num_steps = 200  # Number of steps to take
		change_direction_chance = 0.5
		x, y = map_width // 2, map_height // 2  # Start in the middle of the map

		# Perform the random walk
		current_direction = random.choice(directions)
		for _ in range(num_steps):
			if random.random() < change_direction_chance:
				current_direction = random.choice(directions)
			x = max(1, min(x + current_direction[0], map_width - 2))
			y = max(1, min(y + current_direction[1], map_height - 2))
			dungeon_map[y][x] = 'x'  # Mark the path with 'x'

		# Place the player in the last 'x' position
		dungeon_map[y][x] = 'p'

		# Return the generated map
		return dungeon_map

	def run(self):
		# update and draw the game
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
  
		# create floor
		self.floor_surf = pygame.image.load('graphics/tilemap/ground.png').convert()
		self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

	def custom_draw(self,player):

		# getting the offset 
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height
  
		# draw floor
		floor_offset_pos = self.floor_rect.topleft - self.offset
		self.display_surface.blit(self.floor_surf, floor_offset_pos)

		# for sprite in self.sprites():
		for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image,offset_pos)