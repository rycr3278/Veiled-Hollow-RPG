import pygame
from settings import *
from entity import Entity

class Enemy(Entity):
    enemy_frame_data = {
        'Spider': {'frame_size' : (64,64), 'walk': 8, 'attack': 12, 'death': 17, 'idle': 8, 'hurt' : 6, 'final_death' : 1},
        'Worm': {'frame_size' : (128, 128), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32, 'final_death' : 1, 'waiting' : 1},
        'Skeleton': {'frame_size' : (128,128), 'walk': 8, 'attack': 17, 'death': 13, 'idle': 7, 'hurt' : 11, 'final_death' : 1},
        'BigWorm': {'frame_size' : (128, 128), 'attack': 29, 'death': 12, 'idle': 8, 'hurt' : 8, 'retreat' : 32, 'final_death' : 1, 'waiting' : 1}
    }

    def __init__(self, monster_name, pos, groups, obstacle_sprites):
        # General setup
        super().__init__(groups)
        self.sprite_type = 'enemy'
        self.facing_right = True
        self.facing_right_at_death = True
        self.attacking = False

        # Determine frame size for this monster type
        enemy_type = monster_name.split('/')[0]
        self.monster_type = enemy_type
        frame_width, frame_height = self.enemy_frame_data[enemy_type]['frame_size']

        # Graphics setup
        self.import_graphics(monster_name)  # Import graphics first
        self.frame_index = 0
        
        # Debug: Print the monster_name
        print("Initializing enemy with monster_name:", monster_name)

        # Set initial status based on monster type
        if self.monster_type in ['Worm', 'BigWorm']:
            self.status = 'waiting'
        else:
            self.status = 'idle'
            
        self.image = self.animations[self.status][0]

        self.rect = self.image.get_rect(topleft=pos)

        # Set the initial image based on the frame size
        self.image = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        self.image = self.animations[self.status][self.frame_index]
        
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
        
        # Player Interaction
        self.can_attack = True
        
        # invincibility timer
        self.vulnerable = True
        self.hit_time = None
        self.invincibility_duration = 500
        
    def import_graphics(self, name):
        self.animations = {'walk': [], 'waiting' : [], 'hurt': [], 'attack': [], 'death': [], 'idle': [], 'retreat': [], 'final_death' : []}  # Actions
        
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
                print('this action does not exist')
                # This action does not exist for this enemy type, so we skip it
                pass
   
    def get_image(self, sheet, x, y, width, height):
        # Extracts and returns an image from a sprite sheet
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(sheet, (0,0), (x, y, width, height))
        return image
    
    def animate(self):
        now = pygame.time.get_ticks()
        action = self.status

        if action == 'final_death':
            return  # Exit to prevent further animation

        if action in self.animations and len(self.animations[action]) > 0:
            if now - self.last_update >= self.animation_speed * 1000:
                self.last_update = now
                self.frame_index = (self.frame_index + 1) % len(self.animations[action])
                self.image = self.animations[action][self.frame_index]
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)

                if action == 'hurt' and self.frame_index == len(self.animations['hurt']) - 1:
                    self.status = 'idle'

                if action == 'retreat' and self.frame_index == len(self.animations['retreat']) - 1:
                    self.status = 'waiting'  # Transition back to 'waiting' after 'retreat'

                # Transition from 'death' to 'final_death'
                if action == 'death' and self.frame_index == len(self.animations['death']) - 1:
                    self.status = 'final_death'
                    
    def get_damage(self, player, attack_type):
        current_time = pygame.time.get_ticks()
        if self.vulnerable:
            self.direction = self.get_player_distance_direction(player)[1]
            if attack_type == 'weapon':
                self.health -= player.get_full_weapon_damage()
            else:
                pass # magic damage later
            
            self.hit_time = current_time
            self.vulnerable = False
            
            if self.health <= 0:
                self.status = 'death'
                self.frame_index = 0
                self.final_death_image = self.animations['final_death'][0]
                print('self.facing_right: ', self.facing_right)
                print('self.facing_right_at_death: ', self.facing_right_at_death)
                if not self.facing_right:
                    self.final_death_image = pygame.transform.flip(self.final_death_image, True, False)
                print("Enemy hit: status set to 'death'")
            else:
                self.status = 'hurt'
                self.vulnerable = False
                self.frame_index = 0
                print(f"get_damage: Enemy hurt, setting status to 'hurt', frame index reset to {self.frame_index}")
                print(self.status)
                
    def cooldowns(self):
        current_time = pygame.time.get_ticks()
        if not self.can_attack:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.can_attack = True
                
        if not self.vulnerable:
            if current_time - self.hit_time >= self.invincibility_duration:
                self.vulnerable = True
     
    def check_death(self):
        if self.health <= 0 and self.status != 'final_death':
            if self.status != 'death':
                self.status = 'death'
                self.frame_index = 0  # Start at the first frame of the death animation

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
        distance, _ = self.get_player_distance_direction(player)
        if self.monster_type in ['Worm', 'BigWorm']:
            if self.status == 'waiting' and distance <= self.attack_radius:
                self.status = 'attack'
            elif self.status == 'idle' and distance > self.attack_radius:
                self.status = 'retreat'  # Change to 'retreat' when player leaves attack radius
            elif self.status == 'attack' and self.frame_index == len(self.animations['attack']) - 1:
                self.status = 'idle'
            elif self.status == 'retreat' and self.frame_index == len(self.animations['retreat']) - 1:
                self.status = 'waiting'  # Ensure it goes back to 'waiting' after 'retreat'
        else:
            # Handling for other enemy types
            if self.status == 'hurt':
                return
            if distance <= self.attack_radius and self.can_attack:
                self.status = 'attack'
            elif distance <= self.notice_radius:
                self.status = 'walk'
            else:
                self.status = 'idle'

    def actions(self, player):
        if self.status in ['death', 'final_death']:
            return

        if self.monster_type in ['Worm', 'BigWorm']:
            # Special handling for worms
            if self.status not in ['waiting', 'hurt']:
                self.update_direction(player)
        else:
            # Handling for other enemy types
            if self.status in ['hurt', 'attack']:
                self.direction = pygame.math.Vector2()  # Stop moving when attacking
            elif self.status == 'walk':
                self.update_direction(player)
        
        # Update facing direction
        if self.direction.x < 0:
            self.facing_right = False
        elif self.direction.x > 0:
            self.facing_right = True

    def hit_reaction(self):
        if self.status == 'hurt':
            # The animation logic will be handled in the animate method called in update
            pass

    def update_direction(self, player):
            _, direction = self.get_player_distance_direction(player)
            self.direction = direction

    def move_and_face_direction(self):
        if self.status not in ['attack', 'death', 'final_death']:
            self.move(self.speed)
            # Update facing direction
            if self.direction.x < 0:
                self.facing_right = False
            elif self.direction.x > 0:
                self.facing_right = True

    def update(self):
        #print(f"update: Current status is {self.status}")
        if self.status != 'final_death':
            if self.status != 'hurt':
                self.move_and_face_direction()  # Handle movement and facing direction
            self.animate()
        else:
            if self.facing_right:
                self.image = self.animations['final_death'][0]  # Show the final death frame
            else:
                self.image = pygame.transform.flip(self.animations['final_death'][0], True, False)  # Flip if needed

        self.cooldowns()
        self.check_death()

    def enemy_update(self, player):
        #print(f"enemy_update: Current status is {self.status}")
        if self.status == 'final_death':
            return
        if self.status not in ['final_death', 'death']:
            self.get_status(player)
            self.actions(player)
        self.check_death()

