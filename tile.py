import pygame 
from settings import *

class Tile(pygame.sprite.Sprite):
    # Class attribute to store preloaded images
    preloaded_images = []

    @classmethod
    def preload_images(cls):
        tile_images = [
            'graphics/dungeon/wall/1.png',
            'graphics/dungeon/wall/2.png',
            'graphics/dungeon/wall/3.png',
            'graphics/dungeon/wall/4.png',
            'graphics/dungeon/wall/5.png',
            'graphics/dungeon/wall/6.png'
        ]
        for img_path in tile_images:
            image = pygame.transform.scale(pygame.image.load(img_path), (TILESIZE, TILESIZE)).convert_alpha()
            cls.preloaded_images.append(image)
            # Also store the flipped version
            cls.preloaded_images.append(pygame.transform.flip(image, True, False))

    def __init__(self, pos, groups):
        super().__init__(groups)
        if not Tile.preloaded_images:
            Tile.preload_images()

        self.image = random.choice(Tile.preloaded_images)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10)
