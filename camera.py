import pygame

LOGICAL_WIDTH = 640
LOGICAL_HEIGHT = 480

class MegaManCamera:
    def __init__(self, world_width, world_height, physical_width):
        self.world_width = world_width
        self.world_height = world_height
        self.current_x = 0
        self.current_y = 0
        self.target_x = 0
        self.target_y = 0
        self.screen_width = LOGICAL_WIDTH
        self.screen_height = LOGICAL_HEIGHT
        self.physical_width = physical_width
        self.x_offset = (self.physical_width - self.screen_width) // 2
        self.moving = False
        self.animation_time = 0.5
        self.animation_progress = 0
        self.start_x = 0
        self.start_y = 0
        self.deadzone_top = 120

    def update(self, target, dt):
        new_target_x = (target.rect.centerx // self.screen_width) * self.screen_width
        new_target_x = max(0, min(new_target_x, self.world_width - self.screen_width))

        upper_deadzone = self.current_y + self.deadzone_top
        bottom_limit = self.current_y + self.screen_height

        if target.rect.centery < upper_deadzone:
            new_target_y = (target.rect.centery // self.screen_height) * self.screen_height
        elif target.rect.centery > bottom_limit:
            new_target_y = (target.rect.centery // self.screen_height) * self.screen_height
        else:
            new_target_y = self.target_y

        new_target_y = max(0, min(new_target_y, self.world_height - self.screen_height))

        if (new_target_x != self.target_x or new_target_y != self.target_y) and not self.moving:
            self.target_x = new_target_x
            self.target_y = new_target_y
            self.start_x = self.current_x
            self.start_y = self.current_y
            self.moving = True
            self.animation_progress = 0

        if self.moving:
            self.animation_progress += dt / self.animation_time
            if self.animation_progress >= 1:
                self.animation_progress = 1
                self.moving = False

            t = 1 - (1 - self.animation_progress) ** 3
            self.current_x = self.start_x + (self.target_x - self.start_x) * t
            self.current_y = self.start_y + (self.target_y - self.start_y) * t

    def apply(self, rect):
        return rect.move(-self.current_x + self.x_offset, -self.current_y)

    def get_world_rect(self):
        return pygame.Rect(self.current_x, self.current_y, self.screen_width, self.screen_height)

    def is_moving(self):
        return self.moving

    def set_position(self, x, y):
        clamped_x = max(0, min(x, self.world_width - self.screen_width))
        clamped_y = max(0, min(y, self.world_height - self.screen_height))
        self.current_x = clamped_x
        self.current_y = clamped_y
        self.target_x = clamped_x
        self.target_y = clamped_y
        self.moving = False
        self.animation_progress = 1

    def is_in_camera_view(self, rect):
        # Проверяем видимость в пределах физического экрана, а не логического
        camera_world_rect = pygame.Rect(self.current_x - self.x_offset, self.current_y, self.physical_width, self.screen_height)
        return camera_world_rect.colliderect(rect)