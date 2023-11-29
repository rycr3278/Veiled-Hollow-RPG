import pygame, sys
from settings import *
from level import Level
from debug import *
import os
import cProfile

class Game:
	def __init__(self):
		  
		# general setup
		pygame.init()
		self.screen = pygame.display.set_mode((WIDTH,HEIGHT))
		pygame.display.set_caption('Veiled Hollow')
		self.clock = pygame.time.Clock()
		self.vignette = self.create_vignette_surface((WIDTH, HEIGHT))
		self.level = Level()

	def create_vignette_surface(self, screen_size, intensity=400):
		vignette_surface = pygame.Surface(screen_size).convert_alpha()
		width, height = screen_size

		for x in range(width):
			for y in range(height):
				distance_from_center = ((x - width / 2) ** 2 + (y - height / 2) ** 2) ** 0.5
				max_distance = (width ** 2 + height ** 2) ** 0.5

				alpha = min(intensity * distance_from_center / max_distance, 255)
				vignette_surface.set_at((x, y), (0, 0, 0, alpha))

		return vignette_surface
		for sprite in group:
			if hasattr(sprite, 'hitbox'):
				# If the sprite has a hitbox attribute, draw a box around it
				pygame.draw.rect(screen, color, sprite.hitbox, 1)  # 1 is the width of the box border
			else:
				# Otherwise, draw a box around the sprite's rect
				pygame.draw.rect(screen, color, sprite.rect, 1)

	def run(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()

			self.level.run()
			
			# Draw the vignette over the screen
			self.screen.blit(self.vignette, (0, 0))
			self.level.ui.display(self.level.player)   
			pygame.display.update()
			
			self.clock.tick(FPS)

if __name__ == '__main__':
	game = Game()
 
	game.run()