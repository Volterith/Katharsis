# player.py

import pygame
from vine import Vine
from tiles import BreakableTile

# Константы физики
GRAVITY = 1800 
KNOCKBACK_GRAVITY = 2160
MAX_FALL_SPEED = 600
JUMP_VELOCITY = -720
KNOCKBACK_X_SPEED = 240
KNOCKBACK_Y_SPEED = -360
DASH_BASE_SPEED = 480
DASH_JUMP_SPEED = -180

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, snd_hurt=None, snd_vine=None, snd_jump=None, particles_enabled=True):
        super().__init__()
        self.particles_enabled = particles_enabled
        self.snd_hurt = snd_hurt
        self.snd_vine = snd_vine
        self.snd_jump = snd_jump
        
        try:
            self.original_image = pygame.image.load("Sprites/player.png").convert_alpha()
        except:
            self.original_image = pygame.Surface((32, 64), pygame.SRCALPHA)
            pygame.draw.polygon(self.original_image, (100, 100, 100), [(16, 0), (32, 64), (0, 64)])
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.velocity_y = 0.0
        self.velocity_x = 0.0
        self.on_ground = False
        self.facing_right = True
        self.can_move = True
        
        self.invincible = False
        self.invincible_time = 0.0
        self.invincible_duration = 1.0
        self.hit_stun_time = 0.0
        self.hit_stun_duration = 0.5
        self.max_health = 5
        self.current_health = self.max_health
        self.is_knockback = False
        
        self.attack_cooldown = 0.0
        self.attack_cooldown_max = 0.5
        
        self.is_charging = False
        self.charge_power = 0.0
        self.max_charge_power = 100.0
        self.charge_rate = 80.0
        self.charge_cooldown = 0.0
        self.charge_cooldown_max = 1.5
        self.dashing = False
        self.dash_timer = 0.0
        self.dash_duration = 0.4
        self.dash_speed_multiplier = 2.5
        self.charge_sound_playing = False
        self.dash_damage = 2

        self.charge_bar_width = 60
        self.charge_bar_height = 8
        self.charge_bar_offset = pygame.Vector2(0, -40)
        self.charge_bar_visible = False

        self.jump_buffer_time = 0.15
        self.jump_buffer_timer = 0.0

        self.coyote_time_duration = 0.1
        self.last_on_ground_timer = 0.0

    def take_damage(self, damage, knockback_direction):
        if not self.invincible and self.current_health > 0:
            self.current_health -= damage
            self.velocity_x = knockback_direction * KNOCKBACK_X_SPEED
            self.velocity_y = KNOCKBACK_Y_SPEED
            self.is_knockback = True
            self.invincible = True
            self.invincible_time = self.invincible_duration
            self.hit_stun_time = self.hit_stun_duration
            if self.snd_hurt: self.snd_hurt.play()
            return True
        return False

    def heal(self, amount):
        self.current_health = min(self.max_health, self.current_health + amount)

    def attack(self, vines_group):
        if self.attack_cooldown <= 0 and self.last_on_ground_timer > 0:
            offset_x = 48 if self.facing_right else -48
            vine = Vine(self.rect.centerx + offset_x, self.rect.bottom, self.facing_right)
            vines_group.add(vine)
            self.attack_cooldown = self.attack_cooldown_max
            if self.snd_vine: self.snd_vine.play()
            return True
        return False

    def start_charging(self):
        if (self.charge_cooldown <= 0 and self.on_ground and not self.is_charging and not self.dashing):
            self.is_charging = True
            self.charge_power = 0
            self.velocity_x = 0
            self.charge_bar_visible = True
            if hasattr(self, 'snd_charge'): self.snd_charge.play()

    def stop_charging(self):
        if self.is_charging:
            self.is_charging = False
            self.charge_cooldown = self.charge_cooldown_max
            self.dashing = True
            self.dash_timer = self.dash_duration
            
            self.invincible = True
            self.invincible_time = max(self.invincible_time, self.dash_duration)
            
            self.charge_bar_visible = False
            
            direction = 1 if self.facing_right else -1
            charge_multiplier = 1 + (self.charge_power / self.max_charge_power) * self.dash_speed_multiplier
            self.velocity_x = direction * DASH_BASE_SPEED * charge_multiplier
            self.velocity_y = DASH_JUMP_SPEED
            
            self.charge_power = 0
            if hasattr(self, 'snd_charge') and self.snd_charge.get_num_channels() > 0: self.snd_charge.stop()

    def jump(self):
        self.jump_buffer_timer = self.jump_buffer_time

    def update(self, obstacles, platforms, falling_tiles, world_width, world_height, dt):
        if dt > 0.1: dt = 0.1

        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= dt
        
        if self.on_ground:
            self.last_on_ground_timer = self.coyote_time_duration
        else:
            if self.last_on_ground_timer > 0:
                self.last_on_ground_timer -= dt

        if self.invincible:
            self.invincible_time -= dt
            if self.invincible_time <= 0: self.invincible = False
        
        if self.hit_stun_time > 0:
            self.hit_stun_time -= dt
            self.can_move = False
            if self.hit_stun_time <= 0:
                 self.is_knockback = False
        else:
            self.can_move = True

        if self.attack_cooldown > 0: self.attack_cooldown -= dt
        if self.charge_cooldown > 0: self.charge_cooldown -= dt

        if self.dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.dashing = False
                self.velocity_x *= 0.7

        if self.is_charging:
            self.charge_power = min(self.max_charge_power, self.charge_power + self.charge_rate * dt)

        gravity = KNOCKBACK_GRAVITY if self.is_knockback else GRAVITY
        self.velocity_y += gravity * dt
        if self.velocity_y > MAX_FALL_SPEED: self.velocity_y = MAX_FALL_SPEED

        # *** ИСПРАВЛЕНИЕ: Используем round() вместо int() для корректного округления ***
        self.x += self.velocity_x * dt
        self.rect.x = round(self.x)
        self._handle_horizontal_collisions(obstacles)
        
        self.y += self.velocity_y * dt
        self.rect.y = round(self.y)
        self._handle_vertical_collisions(obstacles, platforms, falling_tiles, world_height, dt)
        
        self._handle_world_bounds(world_width, world_height)

        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        if self.jump_buffer_timer > 0 and self.on_ground:
            self.velocity_y = JUMP_VELOCITY
            if self.snd_jump: self.snd_jump.play()
            self.jump_buffer_timer = 0.0
            self.on_ground = False

    def _handle_horizontal_collisions(self, obstacles):
        hit_list = pygame.sprite.spritecollide(self, obstacles, False)
        for obstacle in hit_list:
            if self.dashing and isinstance(obstacle, BreakableTile):
                if obstacle.take_damage(self.dash_damage, self.particles_enabled):
                    obstacles.remove(obstacle)
                    continue 
            
            if self.velocity_x > 0:
                self.rect.right = obstacle.rect.left
            elif self.velocity_x < 0:
                self.rect.left = obstacle.rect.right
            
            self.x = float(self.rect.x)
            self.velocity_x = 0
            if self.dashing:
                self.dashing = False

    def _handle_vertical_collisions(self, obstacles, platforms, falling_tiles, world_height, dt):
        self.on_ground = False
        hit_list = pygame.sprite.spritecollide(self, obstacles, False)
        for obstacle in hit_list:
            if self.velocity_y > 0:
                self.rect.bottom = obstacle.rect.top
                self.on_ground = True
                self.velocity_y = 0
            elif self.velocity_y < 0:
                self.rect.top = obstacle.rect.bottom
                self.velocity_y = 0
            self.y = float(self.rect.y)
            if hasattr(obstacle, 'properties') and obstacle.properties.get('damage', 0) > 0:
                self.take_damage(obstacle.properties['damage'], -1 if self.rect.centerx < obstacle.rect.centerx else 1)

        platform_hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in platform_hits:
            if self.velocity_y > 0 and (self.y + self.rect.height - self.velocity_y * dt) <= platform.rect.top + 5:
                self.rect.bottom = platform.rect.top
                self.on_ground = True
                self.velocity_y = 0
                self.y = float(self.rect.y)

        falling_hits = pygame.sprite.spritecollide(self, falling_tiles, False)
        for tile in falling_hits:
            if (tile.fall_on_stand and self.velocity_y >= 0 and (self.y + self.rect.height - self.velocity_y * dt) <= tile.rect.top + 5):
                self.rect.bottom = tile.rect.top
                self.on_ground = True
                self.velocity_y = 0
                self.y = float(self.rect.y)
                if not tile.falling and not tile.shaking:
                    tile.start_shaking()
    
    def _handle_world_bounds(self, world_width, world_height):
        if self.x < 0: self.x = 0
        if self.x + self.rect.width > world_width: self.x = world_width - self.rect.width
        if self.y < 0: self.y = 0; self.velocity_y = 0
        if self.y + self.rect.height > world_height:
            self.y = world_height - self.rect.height
            self.on_ground = True
            self.velocity_y = 0
        self.rect.x = round(self.x)
        self.rect.y = round(self.y)

    def flip_image(self, facing_right):
        if facing_right != self.facing_right:
            self.facing_right = facing_right
            self.image = pygame.transform.flip(self.original_image, True, False) if not facing_right else self.original_image

    def draw_charge_bar(self, surface, camera):
        if self.charge_bar_visible and self.is_charging:
            screen_pos = camera.apply(self.rect).center + self.charge_bar_offset
            bg_rect = pygame.Rect(0, 0, self.charge_bar_width, self.charge_bar_height)
            bg_rect.center = screen_pos
            pygame.draw.rect(surface, (30, 30, 30), bg_rect, border_radius=5)
            charge_width = int(self.charge_bar_width * (self.charge_power / self.max_charge_power))
            if charge_width > 0:
                charge_rect = pygame.Rect(0, 0, charge_width, self.charge_bar_height - 2)
                charge_rect.midleft = (bg_rect.left + 1, bg_rect.centery)
                charge_color = (int(255 * (1 - self.charge_power / self.max_charge_power)), int(255 * (self.charge_power / self.max_charge_power)), 0)
                pygame.draw.rect(surface, charge_color, charge_rect, border_radius=3)
            pygame.draw.rect(surface, (150, 150, 150), bg_rect, 1, border_radius=5)

    def handle_event(self, event):
        pass