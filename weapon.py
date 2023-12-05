import pygame

class Weapon(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        super().__init__(groups)
        self.sprite_type = 'weapon'
        direction = player.status
        
        # graphic
        full_path = f'graphics/weapons/{player.weapon}/{direction}.png'
        original_image = pygame.image.load(full_path).convert_alpha()
        
        # Create a red box of the same size as the weapon's image
        self.image = original_image
        #self.image.fill((255, 0, 0))  # Fill with red color
        
        # placement
        if direction == 'right':
            self.rect = self.image.get_rect(center = player.rect.midright + pygame.math.Vector2(16,0))
        elif direction == 'left':
            self.rect = self.image.get_rect(center = player.rect.midleft - pygame.math.Vector2(16,0))
        elif direction == 'up':
            self.rect = self.image.get_rect(center = player.rect.midtop + pygame.math.Vector2(16,0))
        else:
            self.rect = self.image.get_rect(center = player.rect.midbottom - pygame.math.Vector2(16,0))