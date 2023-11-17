import pygame 
from settings import *

class Tile(pygame.sprite.Sprite):
    tilesheets = {}

    @classmethod
    def load_tilesheet(cls, key, path):
        tilesheet = pygame.image.load(path).convert_alpha()
        cls.tilesheets[key] = tilesheet

    def __init__(self, pos, visible_group, obstacle_group, tilesheet_key, tile_coordinates, tile_type, edge_type = None):
        super().__init__(visible_group)  # Add to visible group
        tilesheet = Tile.tilesheets[tilesheet_key]
        x, y = tile_coordinates
        tile_size = 32  # Assuming each tile is 32x32
        rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
        self.image = tilesheet.subsurface(rect)
        self.rect = self.image.get_rect(topleft=pos)
        
        self.is_floor = tile_type == 'floor'
        self.is_wall = tile_type == 'wall'
        self.is_overlay = tile_type == 'overlay'
        self.is_corner_tile = tile_type == 'corner'
        self.edge_type = edge_type

        if self.is_corner_tile:
            print(f"Corner tile created at: {self.rect.topleft}")


        if self.is_wall:
            # Only add wall tiles to the obstacle group and set a custom hitbox
            self.add(obstacle_group)
            self.hitbox = self.rect.inflate(22,20)
        else:
            # For floor tiles, the hitbox is the same as the rect
            self.hitbox = self.rect

