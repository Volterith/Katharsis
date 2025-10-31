import pygame

class Vine(pygame.sprite.Sprite):
    def __init__(self, x, y, facing_right):
        super().__init__()
        try:
            self.image = pygame.image.load("Sprites/vine.png").convert_alpha()
        except:
            self.image = pygame.Surface((32, 64), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (0, 150, 0), (0, 0, 32, 64))
        
        if not facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
        
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.lifetime = 1.0  # Время жизни в секундах
        self.growth_time = 0.2  # Время роста
        self.state = "growing"  # growing, active, retreating
        self.state_time = 0
        self.max_height = self.rect.height
        self.original_y = y

    def update(self, dt):
        self.state_time += dt
        
        if self.state == "growing":
            # Анимация роста
            progress = min(1.0, self.state_time / self.growth_time)
            self.rect.height = int(self.max_height * progress)
            self.rect.y = self.original_y - self.rect.height
            
            if progress >= 1.0:
                self.state = "active"
                self.state_time = 0
                
        elif self.state == "active":
            # Ожидание перед исчезновением
            if self.state_time >= self.lifetime:
                self.state = "retreating"
                self.state_time = 0
                
        elif self.state == "retreating":
            # Анимация исчезновения
            progress = min(1.0, self.state_time / self.growth_time)
            self.rect.height = int(self.max_height * (1 - progress))
            self.rect.y = self.original_y - self.rect.height
            
            if progress >= 1.0:
                self.kill()