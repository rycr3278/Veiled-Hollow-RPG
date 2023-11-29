import pygame
pygame.init()
font = pygame.font.Font(None,30)

def debug(info,y = 10, x = 10):
	display_surface = pygame.display.get_surface()
	debug_surf = font.render(str(info),True,'White')
	debug_rect = debug_surf.get_rect(topleft = (x,y))
	pygame.draw.rect(display_surface,'Black',debug_rect)
	display_surface.blit(debug_surf,debug_rect)
 
def draw_debug_boxes(group, screen, color=(255, 0, 0)):
    for sprite in group:
        if hasattr(sprite, 'hitbox'):
            pygame.draw.rect(screen, color, sprite.hitbox, 1)
        else:
            pygame.draw.rect(screen, color, sprite.rect, 1)