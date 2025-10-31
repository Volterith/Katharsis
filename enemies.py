# enemies.py

import pygame
import math

GRAVITY = 1800 

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, sprite_width, sprite_height, properties=None):
        super().__init__()
        self.properties = properties or {}
        try:
            self.original_image_sheet = pygame.image.load(image_path).convert_alpha()
        except pygame.error:
            print(f"Warning: Could not load image {image_path}. Using placeholder.")
            self.original_image_sheet = pygame.Surface((sprite_width * 4, sprite_height), pygame.SRCALPHA)
            self.original_image_sheet.fill((255, 0, 255))
            pygame.draw.rect(self.original_image_sheet, (0, 0, 0), (0, 0, sprite_width, sprite_height), 1)

        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.animation_frames = []
        self.current_frame = 0
        self.animation_speed = 0.15
        self.last_update = pygame.time.get_ticks()

        self._load_animation_frames()
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect(topleft=(x, y))

        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False
        self.current_health = self.properties.get('health', 3)
        self.max_health = self.current_health
        self.damage = self.properties.get('damage', 1)
        self.knockback_power = self.properties.get('knockback', 300)
        self.facing_right = True
        self.invincible = False
        self.invincible_time = 0.5
        self.invincible_timer = 0.0

        self.state = "idle"
        self.attack_cooldown = 0.0
        self.attack_cooldown_max = 1.0
        self.attack_range = 50
        self.attack_timer = 0.0
        self.attack_duration = 0.5
        self.attack_animation_time = 0.0
        self.attack_animation_max_time = 0.4

        self.dying = False
        self.death_timer = 0.0
        self.death_duration = 0.5
        self.initial_alpha = 255
        self.death_scale = 1.0

    def _load_animation_frames(self):
        frame_count = self.original_image_sheet.get_width() // self.sprite_width
        for i in range(frame_count):
            if i * self.sprite_width + self.sprite_width <= self.original_image_sheet.get_width():
                frame = self.original_image_sheet.subsurface(
                    (i * self.sprite_width, 0, self.sprite_width, self.sprite_height)
                )
                self.animation_frames.append(frame)
            else:
                print(f"Warning: Frame index {i} out of bounds for image sheet of width {self.original_image_sheet.get_width()} and sprite width {self.sprite_width}.")

    def update_animation(self):
        if self.dying:
            return

        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed * 1000:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            
            base_frame = self.animation_frames[self.current_frame]
            if not self.facing_right:
                self.image = pygame.transform.flip(base_frame, True, False)
            else:
                self.image = base_frame.copy()

        if self.invincible:
            if math.sin(self.invincible_timer * 40) > 0:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def take_damage(self, damage, knockback_direction):
        if not self.invincible and not self.dying:
            self.current_health -= damage
            self.invincible = True
            self.invincible_timer = self.invincible_time
            self.state = "hurt"
            self.velocity_x = knockback_direction * self.knockback_power
            self.velocity_y = -self.knockback_power / 2
            if self.current_health <= 0:
                self.start_death_animation()
            return True
        return False

    def start_death_animation(self):
        self.dying = True
        self.state = "dying"
        self.death_timer = 0.0
        self.velocity_x = 0
        self.velocity_y = 0
        self.image.set_alpha(self.initial_alpha)
        self.death_scale = 1.0

    def update(self, obstacles, platforms, player, world_width, world_height, dt):
        if dt > 0.1: dt = 0.1

        if self.dying:
            self.death_timer += dt
            progress = self.death_timer / self.death_duration
            if progress >= 1.0:
                self.kill()
                return
            current_alpha = int(self.initial_alpha * (1 - progress))
            self.death_scale = 1.0 - (progress * 0.5)

            base_frame = self.animation_frames[self.current_frame]

            if base_frame.get_width() > 0 and base_frame.get_height() > 0:
                try:
                    scaled_image = pygame.transform.scale(
                        base_frame,
                        (int(self.sprite_width * self.death_scale), int(self.sprite_height * self.death_scale))
                    )
                    if not self.facing_right:
                        scaled_image = pygame.transform.flip(scaled_image, True, False)
                    self.image = scaled_image
                    self.image.set_alpha(current_alpha)
                    old_center = self.rect.center
                    self.rect = self.image.get_rect(center=old_center)
                except ValueError:
                   return
            return

        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0: self.invincible = False

        if self.attack_cooldown > 0: self.attack_cooldown -= dt
        if self.state == "attacking":
            self.attack_animation_time += dt
            if self.attack_animation_time >= self.attack_animation_max_time:
                self.state = "idle"
                self.attack_animation_time = 0

        self.velocity_y += GRAVITY * dt
        if self.velocity_y > 600: self.velocity_y = 600

        # *** ИСПРАВЛЕНИЕ: Используем round() вместо int() для корректного округления ***
        self.x += self.velocity_x * dt
        self.rect.x = round(self.x)
        self._handle_horizontal_collisions(obstacles)

        self.y += self.velocity_y * dt
        self.rect.y = round(self.y)
        self._handle_vertical_collisions(obstacles, platforms)
        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self._handle_world_bounds(world_width)

        self.ai_update(player, dt)
        self.update_animation()

    def _handle_horizontal_collisions(self, obstacles):
        hit_list = pygame.sprite.spritecollide(self, obstacles, False)
        for obstacle in hit_list:
            if self.velocity_x > 0: self.rect.right = obstacle.rect.left
            elif self.velocity_x < 0: self.rect.left = obstacle.rect.right
            self.x = float(self.rect.x)
            self.velocity_x = 0

    def _handle_vertical_collisions(self, obstacles, platforms):
        self.on_ground = False
        hit_list = pygame.sprite.spritecollide(self, obstacles, False)
        for obstacle in hit_list:
            if self.velocity_y > 0:
                self.rect.bottom = obstacle.rect.top
                self.on_ground = True
            elif self.velocity_y < 0:
                self.rect.top = obstacle.rect.bottom
            self.y = float(self.rect.y)
            self.velocity_y = 0

        platform_hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in platform_hits:
            if self.velocity_y > 0 and self.rect.bottom <= platform.rect.top + 5:
                self.rect.bottom = platform.rect.top
                self.on_ground = True
                self.y = float(self.rect.y)
                self.velocity_y = 0
    
    def _handle_world_bounds(self, world_width):
        if self.x < 0:
            self.x = 0
            if self.velocity_x < 0: self.velocity_x = 0
        if self.x + self.rect.width > world_width:
            self.x = world_width - self.rect.width
            if self.velocity_x > 0: self.velocity_x = 0
        
        self.rect.x = round(self.x)

    def ai_update(self, player, dt):
        pass

    def draw_health_bar(self, surface, camera):
        if self.current_health < self.max_health and not self.dying:
            screen_pos = camera.apply(self.rect).topleft
            bar_width = self.rect.width
            bar_height = 5
            health_ratio = self.current_health / self.max_health
            bg_rect = pygame.Rect(screen_pos[0], screen_pos[1] - bar_height - 5, bar_width, bar_height)
            health_rect = pygame.Rect(screen_pos[0], screen_pos[1] - bar_height - 5, bar_width * health_ratio, bar_height)
            pygame.draw.rect(surface, (255, 0, 0), bg_rect)
            pygame.draw.rect(surface, (0, 255, 0), health_rect)
            pygame.draw.rect(surface, (0, 0, 0), bg_rect, 1)

class MeleeGhost(Enemy):
    def __init__(self, x, y, properties=None):
        super().__init__(x, y, "Sprites/closecombat_ghost.png", 64, 64, properties)
        self.speed = self.properties.get('speed', 120)
        self.attack_range = 40
        self.damage = self.properties.get('damage', 1)
        self.knockback_power = self.properties.get('knockback', 480)
        self.attack_cooldown_max = 1.5
        self.animation_speed = 0.1

    def _load_animation_frames(self):
        for i in range(4):
            if i * self.sprite_width + self.sprite_width <= self.original_image_sheet.get_width():
                frame = self.original_image_sheet.subsurface((i * self.sprite_width, 0, self.sprite_width, self.sprite_height))
                self.animation_frames.append(frame)

    def ai_update(self, player, dt):
        if self.state == "hurt":
            if abs(self.velocity_x) < 1:
                self.velocity_x = 0
                self.state = "idle"
            else:
                self.velocity_x *= 0.95
            return

        distance_to_player = math.hypot(self.rect.centerx - player.rect.centerx, self.rect.centery - player.rect.centery)

        if distance_to_player < 200:
            if distance_to_player > self.attack_range:
                if self.rect.centerx < player.rect.centerx:
                    self.velocity_x = self.speed
                    self.facing_right = True
                else:
                    self.velocity_x = -self.speed
                    self.facing_right = False
                self.state = "moving"
            else:
                self.velocity_x = 0
                if self.attack_cooldown <= 0:
                    self.attack(player)
                    self.attack_cooldown = self.attack_cooldown_max
                    self.state = "attacking"
                else:
                    self.state = "idle"
        else:
            self.velocity_x = 0
            self.state = "idle"

    def attack(self, player):
        if abs(self.rect.centerx - player.rect.centerx) < self.attack_range and abs(self.rect.centery - player.rect.centery) < self.rect.height / 2:
            knockback_dir = 1 if player.rect.centerx > self.rect.centerx else -1
            player.take_damage(self.damage, knockback_dir)

class RangedGhost(Enemy):
    def __init__(self, x, y, properties=None):
        super().__init__(x, y, "Sprites/longrangecombat_ghost_afk.png", 64, 64, properties)
        self.speed = self.properties.get('speed', 60)
        self.attack_range = 150
        self.damage = self.properties.get('damage', 1)
        self.knockback_power = self.properties.get('knockback', 300)
        self.attack_cooldown_max = 2.0
        self.projectile_speed = 300
        self.projectiles = pygame.sprite.Group()
        self.animation_speed = 0.15
        
        try:
            self.attack_animation_sheet = pygame.image.load("Sprites/longrangecombat_ghost_attack.png").convert_alpha()
        except pygame.error:
            self.attack_animation_sheet = pygame.Surface((self.sprite_width * 4, self.sprite_height), pygame.SRCALPHA)
            self.attack_animation_sheet.fill((255, 100, 255))
        
        self.idle_animation_frames = self.animation_frames[:]
        self.attack_animation_frames = []
        self._load_attack_animation_frames()
        self.attack_animation_duration = 0.6
        self.attack_animation_timer = 0.0

    def _load_attack_animation_frames(self):
        for i in range(4):
            if i * self.sprite_width + self.sprite_width <= self.attack_animation_sheet.get_width():
                frame = self.attack_animation_sheet.subsurface((i * self.sprite_width, 0, self.sprite_width, self.sprite_height))
                self.attack_animation_frames.append(frame)

    def update_animation(self):
        if self.dying: return

        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed * 1000:
            self.last_update = now
            
            if self.state == "attacking":
                if self.current_frame < len(self.attack_animation_frames) - 1:
                    self.current_frame += 1
                base_frame = self.attack_animation_frames[self.current_frame]
            else:
                self.current_frame = (self.current_frame + 1) % len(self.idle_animation_frames)
                base_frame = self.idle_animation_frames[self.current_frame]
            
            if not self.facing_right:
                self.image = pygame.transform.flip(base_frame, True, False)
            else:
                self.image = base_frame.copy()

        if self.invincible:
            if math.sin(self.invincible_timer * 40) > 0:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def ai_update(self, player, dt):
        if self.state == "hurt":
            if abs(self.velocity_x) < 1:
                self.velocity_x = 0
                self.state = "idle"
            else:
                self.velocity_x *= 0.95
            return

        distance_to_player = math.hypot(self.rect.centerx - player.rect.centerx, self.rect.centery - player.rect.centery)

        if distance_to_player < 300:
            if distance_to_player > self.attack_range:
                if self.rect.centerx < player.rect.centerx:
                    self.velocity_x = self.speed
                    self.facing_right = True
                else:
                    self.velocity_x = -self.speed
                    self.facing_right = False
                self.state = "moving"
            else:
                self.velocity_x = 0
                if self.attack_cooldown <= 0:
                    self.state = "attacking"
                    self.current_frame = 0
                    self.attack(player)
                    self.attack_cooldown = self.attack_cooldown_max
                    self.attack_animation_timer = 0
                elif self.state == "attacking":
                    self.attack_animation_timer += dt
                    if self.attack_animation_timer >= self.attack_animation_duration:
                        self.state = "idle"
                else:
                    self.state = "idle"
        else:
            self.velocity_x = 0
            self.state = "idle"

    def attack(self, player):
        direction_x = player.rect.centerx - self.rect.centerx
        direction_y = player.rect.centery - self.rect.centery
        angle = math.atan2(direction_y, direction_x)
        
        projectile_velocity_x = self.projectile_speed * math.cos(angle)
        projectile_velocity_y = self.projectile_speed * math.sin(angle)
        
        projectile = EnemyProjectile(self.rect.centerx, self.rect.centery, projectile_velocity_x, projectile_velocity_y, self.damage)
        self.projectiles.add(projectile)

    def update(self, obstacles, platforms, player, world_width, world_height, dt):
        super().update(obstacles, platforms, player, world_width, world_height, dt)
        self.projectiles.update(obstacles, player, dt)

class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, velocity_x, velocity_y, damage):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 255), (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.damage = damage
        self.lifetime = 3.0
        self.timer = 0.0

    def update(self, obstacles, player, dt):
        if dt > 0.1: dt = 0.1

        self.timer += dt
        if self.timer >= self.lifetime:
            self.kill()
            return

        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        # *** ИСПРАВЛЕНИЕ: Используем round() вместо int() для корректного округления ***
        self.rect.x = round(self.x)
        self.rect.y = round(self.y)

        if pygame.sprite.spritecollideany(self, obstacles):
            self.kill()
            return

        if self.rect.colliderect(player.rect):
            knockback_dir = 1 if player.rect.centerx > self.rect.centerx else -1
            player.take_damage(self.damage, knockback_dir)
            self.kill()

class EtherJumperBoss(Enemy):
    def __init__(self, x, y, properties=None):
        super().__init__(x, y, "Sprites/boss_idle.png", 140, 120, properties)
        self.max_health = self.properties.get('health', 25)
        self.current_health = self.max_health
        self.speed = self.properties.get('speed', 180)
        self.jump_power = self.properties.get('jump_power', 900)
        self.fall_speed = self.properties.get('fall_speed', 1200)
        self.ground_shake_radius = self.properties.get('shake_radius', 150)
        self.ground_shake_knockback = self.properties.get('shake_knockback', 600)
        self.ground_shake_damage = self.properties.get('shake_damage', 1)
        self.attack_range = 200
        self.attack_cooldown_max = 2.0

        self.state = "inactive"
        self.jump_cooldown = 2.0
        self.jump_timer = 0.0
        self.jump_delay = 0.5
        self.active = False
        self.attack_cooldown = 0.0

        self.idle_animation_frames = []
        self.jump_animation_frames = []
        self._load_animations()
        self.animation_frames = self.idle_animation_frames
        self.current_frame = 0
        self.animation_speed = 0.1

    def _load_animations(self):
        try:
            idle_sheet = pygame.image.load("Sprites/boss_idle.png").convert_alpha()
            frame_count = idle_sheet.get_width() // self.sprite_width
            for i in range(frame_count):
                if i * self.sprite_width + self.sprite_width <= idle_sheet.get_width():
                    frame = idle_sheet.subsurface((i * self.sprite_width, 0, self.sprite_width, self.sprite_height))
                    self.idle_animation_frames.append(frame)
        except:
            print("Failed to load boss idle animation")
            self.idle_animation_frames = [pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)]
            self.idle_animation_frames[0].fill((255, 0, 0))

        try:
            jump_sheet = pygame.image.load("Sprites/boss_jump.png").convert_alpha()
            frame_count = jump_sheet.get_width() // self.sprite_width
            for i in range(frame_count):
                if i * self.sprite_width + self.sprite_width <= jump_sheet.get_width():
                    frame = jump_sheet.subsurface((i * self.sprite_width, 0, self.sprite_width, self.sprite_height))
                    self.jump_animation_frames.append(frame)
        except:
            print("Failed to load boss jump animation")
            self.jump_animation_frames = [pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)]
            self.jump_animation_frames[0].fill((0, 0, 255))

    def update_animation(self):
        if self.dying:
            return

        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed * 1000:
            self.last_update = now
            
            if self.state in ["jumping", "falling"]:
                self.animation_frames = self.jump_animation_frames
            else:
                self.animation_frames = self.idle_animation_frames
            
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            base_frame = self.animation_frames[self.current_frame]

            # *** ИСПРАВЛЕНИЕ: Инвертированная логика отражения, так как исходный спрайт смотрит влево ***
            if self.facing_right:
                # Если нужно смотреть вправо, а спрайт смотрит влево - отражаем
                self.image = pygame.transform.flip(base_frame, True, False)
            else:
                # Если нужно смотреть влево, и спрайт уже смотрит влево - просто копируем
                self.image = base_frame.copy()
        
        if self.invincible:
            if math.sin(self.invincible_timer * 40) > 0:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def update(self, obstacles, platforms, player, world_width, world_height, dt):
        if not self.active:
            distance_to_player = math.hypot(self.rect.centerx - player.rect.centerx, self.rect.centery - player.rect.centery)
            activation_range = 400
            # У босса нет камеры, поэтому убираем player.camera
            if self.rect.colliderect(player.rect) or distance_to_player < activation_range:
                self.active = True
                self.state = "idle"
        
        if self.active:
            if self.attack_cooldown > 0: self.attack_cooldown -= dt
            super().update(obstacles, platforms, player, world_width, world_height, dt)

    def ai_update(self, player, dt):
        if not self.active or self.dying: return

        if self.state == "hurt":
            if abs(self.velocity_x) < 1:
                self.velocity_x = 0
                self.state = "idle"
            else:
                self.velocity_x *= 0.95
            return

        self.jump_timer -= dt

        if self.state == "idle":
            self.velocity_x = 0
            if self.jump_timer <= 0 and self.on_ground:
                self.state = "preparing_jump"
                self.jump_timer = self.jump_delay

        elif self.state == "preparing_jump":
            if self.jump_timer <= 0:
                self.state = "jumping"
                self.velocity_y = -self.jump_power
                self.facing_right = player.rect.centerx > self.rect.centerx
                self.velocity_x = self.speed if self.facing_right else -self.speed
                
        elif self.state == "jumping":
            if self.velocity_y >= 0:
                self.state = "falling"
                # Убрано self.velocity_y = self.fall_speed, так как гравитация уже работает

        elif self.state == "falling":
            if self.on_ground:
                self.state = "landing"
                self.velocity_x = 0
                self.jump_timer = self.jump_cooldown
                self._perform_ground_shake(player)

        elif self.state == "landing":
            if self.jump_timer <= self.jump_cooldown - 0.5:
                self.state = "idle"

        distance_to_player = math.hypot(self.rect.centerx - player.rect.centerx, self.rect.centery - player.rect.centery)
        if self.state == "idle" and distance_to_player < self.attack_range and self.attack_cooldown <= 0:
            self.attack(player)
            self.attack_cooldown = self.attack_cooldown_max

    def attack(self, player):
        self.facing_right = player.rect.centerx > self.rect.centerx
        self.velocity_x = self.speed * 1.5 if self.facing_right else -self.speed * 1.5
        self.velocity_y = -self.jump_power * 0.8
        self.state = "jumping"

    def _perform_ground_shake(self, player):
        distance = math.hypot(self.rect.centerx - player.rect.centerx, self.rect.centery - player.rect.centery)
        if distance < self.ground_shake_radius:
            knockback_dir = 1 if player.rect.centerx > self.rect.centerx else -1
            player.take_damage(self.ground_shake_damage, knockback_dir)

    def draw_health_bar(self, surface, camera):
        # Рисуем полоску только если босс активирован
        if self.active and self.current_health > 0 and not self.dying:
            bar_width = 300
            bar_height = 15
            screen_x = (surface.get_width() - bar_width) // 2
            screen_y = surface.get_height() - bar_height - 15
            
            health_ratio = self.current_health / self.max_health
            
            bg_rect = pygame.Rect(screen_x, screen_y, bar_width, bar_height)
            pygame.draw.rect(surface, (50, 50, 50), bg_rect, border_radius=5)
            
            health_rect = pygame.Rect(screen_x, screen_y, bar_width * health_ratio, bar_height)
            health_color = (int(255 * (1 - health_ratio)), int(255 * health_ratio), 0)
            pygame.draw.rect(surface, health_color, health_rect, border_radius=5)
            
            pygame.draw.rect(surface, (255, 255, 255), bg_rect, 2, border_radius=5)

    def start_death_animation(self):
        super().start_death_animation()