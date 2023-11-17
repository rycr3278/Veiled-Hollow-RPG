import pygame
from settings import *
from entity import Entity

class Enemy(Entity):
    enemy_frame_data = {
        'Spider': {'frame_size' : (64,64), 'walk': 8, 'attack': 12, 'death': 17, 'idle': 8, 'hurt' : 6},
        'Worm': {'frame_size' : (128, 128), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32},
        'Skeleton': {'frame_size' : (128,128), 'walk': 8, 'attack': 17, 'death': 13, 'idle': 7, 'hurt' : 11},
        'BigWorm': {'frame_size' : (128, 128), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32}
    }

    def __init__(self, monster_name, pos, groups, obstacle_sprites):
        # General setup
        super().__init__(groups)
        self.sprite_type = 'enemy'

        # Determine frame size for this monster type
        enemy_type = monster_name.split('/')[0]
        frame_width, frame_height = self.enemy_frame_data[enemy_type]['frame_size']

        # Graphics setup
        self.import_graphics(monster_name)
        self.status = 'idle'  # Set default status
        self.frame_index = 0

        # Set the initial image based on the frame size
        self.image = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)
        
        # Animation setup
        self.last_update = pygame.time.get_ticks()
        
        # Movement
        self.rect = self.image.get_rect(topleft = pos)
        self.hitbox = self.rect.inflate(0, -10)
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
        
    def import_graphics(self, name):
        self.animations = {'walk': [], 'hurt': [], 'attack': [], 'death': [], 'idle': [], 'retreat': []}  # Actions
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

        self.image = self.animations['idle'][0]  # Set initial image
   
    def get_image(self, sheet, x, y, width, height):
        # Extracts and returns an image from a sprite sheet
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(sheet, (0,0), (x, y, width, height))
        return image
    
    def animate(self, action):
        now = pygame.time.get_ticks()
        if action in self.animations and self.animations[action]:  # Check if action exists and has frames
            if now - self.last_update >= self.animation_speed * 1000:
                self.last_update = now
                self.frame_index = (self.frame_index + 1) % len(self.animations[action])
                self.image = self.animations[action][self.frame_index]

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
        distance = self.get_player_distance_direction(player)[0]
        
        if distance <= self.attack_radius:
            self.status = 'attack'
        elif distance <= self.notice_radius:
            self.status = 'move'
        else:
            self.status = 'idle'

    def actions(self, player):
        if self.status == 'attack':
            print('attack')
        elif self.status == 'move':
            self.direction = self.get_player_distance_direction(player)[1]
        else:
            self.direction = pygame.math.Vector2()
    
    def update(self):
        
        self.move(self.speed)
        self.animate(self.status)  # Example, change 'walk' to the desired action
    
    def enemy_update(self, player):
        self.get_status(player)
        self.actions(player)

