import pygame 
from settings import *

class Tile(pygame.sprite.Sprite):
	def __init__(self,pos,groups):
		super().__init__(groups)
		self.tile_images = [
			'graphics/dungeon/wall/1.png',
			'graphics/dungeon/wall/2.png',
			'graphics/dungeon/wall/3.png',
			'graphics/dungeon/wall/4.png',
			'graphics/dungeon/wall/5.png',
			'graphics/dungeon/wall/6.png'
		]
		flip_image = random.choice([True, False])
		chosen_image = random.choice(self.tile_images)
		self.image = pygame.transform.scale(pygame.transform.flip(pygame.image.load(chosen_image), flip_image, False), (TILESIZE, TILESIZE)).convert_alpha()

		self.rect = self.image.get_rect(topleft = pos)
		self.hitbox = self.rect.inflate(0,-10)