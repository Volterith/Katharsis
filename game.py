# game.py

import pygame
from camera import MegaManCamera
from player import Player
from tiles import MapLoader, BreakableTile
from ui import UIManager
from vine import Vine
from enemies import MeleeGhost, RangedGhost, EtherJumperBoss

class Game:
    def __init__(self, screen, particles_enabled=True):
        self.screen = screen
        self.particles_enabled = particles_enabled
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)
        self.channel_bg_music = pygame.mixer.Channel(0)
        self.channel_player_charge = pygame.mixer.Channel(1)
        self.channel_player_actions = pygame.mixer.Channel(2)
        self.channel_collectables = pygame.mixer.Channel(3)
        self.channel_healing = pygame.mixer.Channel(4)
        self.channel_boss_outro = pygame.mixer.Channel(5)
        
        self.clock = pygame.time.Clock()
        self.paused = False
        self.game_over = False
        self.vines = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.boss = None
        self.controls = {}

        self.music_volume = 0.5
        self.sfx_volume = 0.7
        
        self.load_sounds()
        
        self.bg_music = pygame.mixer.Sound("Music/forest.mp3")
        self.bg_music.set_volume(self.music_volume)
        self.boss_music = pygame.mixer.Sound("Music/boss.mp3")
        self.boss_music.set_volume(self.music_volume)

        self.boss_visible = False
        self.current_bg_music = self.bg_music
        
        self.reset_game()

        self.boss_defeated = False
        self.fade_alpha = 0
        self.fading_to_black = False
        self.fading_from_black = False
        self.fade_callback = None

    def load_sounds(self):
        self.snd_jump = pygame.mixer.Sound("Sounds/jump.wav")
        self.snd_hurt = pygame.mixer.Sound("Sounds/hurt.wav")
        self.snd_vine = pygame.mixer.Sound("Sounds/vine.wav")
        self.snd_coin = pygame.mixer.Sound("Sounds/coin.wav")
        self.snd_charge = pygame.mixer.Sound("Sounds/charge.wav")
        self.snd_dash = pygame.mixer.Sound("Sounds/dash.wav")
        self.snd_falling = pygame.mixer.Sound("Sounds/falling.wav")
        self.snd_heal = pygame.mixer.Sound("Sounds/heal.wav")
        self.set_sfx_volume(self.sfx_volume)

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        self.bg_music.set_volume(self.music_volume)
        self.boss_music.set_volume(self.music_volume)
        if self.channel_bg_music.get_sound():
             self.channel_bg_music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in [self.snd_jump, self.snd_hurt, self.snd_vine, self.snd_coin, self.snd_charge, self.snd_dash, self.snd_falling, self.snd_heal]:
            if sound: sound.set_volume(self.sfx_volume)

    def reset_game(self):
        self.map_loader = MapLoader()
        self.map_loader.load_map("Rooms/map.tmx")
        self.player = Player(*self.map_loader.player_spawn_pos,
                             snd_hurt=self.snd_hurt,
                             snd_vine=self.snd_vine,
                             snd_jump=self.snd_jump,
                             particles_enabled=self.particles_enabled)
        self.player.snd_charge = self.snd_charge
        self.player.snd_dash = self.snd_dash
        self.camera = MegaManCamera(self.map_loader.map_width, self.map_loader.map_height, self.screen.get_width())
        self.camera.set_position(self.player.rect.centerx - self.camera.screen_width // 2, self.player.rect.centery - self.camera.screen_height // 2)
        
        self.ui = UIManager()
        self.ui.player = self.player
        self.ui.start_intro()
        self.game_over = False
        self.vines.empty()
        self.enemies.empty()
        self.enemy_projectiles.empty()
        self.boss = None
        self.boss_visible = False
        self.current_bg_music = self.bg_music
        
        self.channel_bg_music.stop()

        for enemy_data in self.map_loader.enemies_data:
            enemy_type = enemy_data['type']
            x, y = enemy_data['pos']
            properties = enemy_data['properties']
            if enemy_type == "MeleeGhost": self.enemies.add(MeleeGhost(x, y, properties))
            elif enemy_type == "RangedGhost": self.enemies.add(RangedGhost(x, y, properties))
            elif enemy_type == "EtherJumperBoss":
                self.boss = EtherJumperBoss(x, y, properties)
                self.enemies.add(self.boss)

        self.update_breakable_tiles_collidable_state()
        self.boss_defeated = False
        self.fading_to_black = False
        self.fading_from_black = False

    def update_breakable_tiles_collidable_state(self):
        non_boss_enemies_exist = any(not isinstance(enemy, EtherJumperBoss) for enemy in self.enemies)
        for tile in self.map_loader.breakable_tiles:
            if tile.properties.get('boss_dependent', False):
                is_collidable = non_boss_enemies_exist
                if tile.collidable != is_collidable:
                    tile.collidable = is_collidable
                    if is_collidable:
                        if tile not in self.map_loader.obstacles: self.map_loader.obstacles.add(tile)
                    else:
                        tile.remove(self.map_loader.obstacles)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.ui.showing_intro:
                if event.key == pygame.K_RETURN and self.ui.show_prompt:
                    self.ui.skip_intro()
                    self.channel_bg_music.play(self.bg_music, -1)
                return
            if self.paused or self.fading_to_black or self.fading_from_black: return

            if event.key == self.controls.get('jump'):
                self.player.jump() 
            
            if event.key == self.controls.get('attack') and not self.player.is_charging:
                if self.player.attack(self.vines): self.channel_player_actions.play(self.snd_vine)

    def handle_input(self, controls):
        self.controls = controls
        if self.paused or self.game_over or self.ui.showing_intro or self.fading_to_black or self.fading_from_black: return

        keys = pygame.key.get_pressed()
        MOVE_SPEED = 250 

        if not self.player.dashing and not self.player.is_knockback:
            if self.player.is_charging:
                self.player.velocity_x = 0
            else:
                # *** ИСПРАВЛЕНИЕ: Улучшенная логика обработки ввода ***
                move_direction = 0
                if keys[self.controls.get('move_left', -1)]:
                    move_direction -= 1
                if keys[self.controls.get('move_right', -1)]:
                    move_direction += 1
                
                self.player.velocity_x = move_direction * MOVE_SPEED
                
                if move_direction > 0:
                    self.player.flip_image(True)
                elif move_direction < 0:
                    self.player.flip_image(False)
        
        if keys[self.controls.get('charge', -1)]:
            if not self.player.is_charging and self.player.on_ground and self.player.charge_cooldown <= 0: self.player.start_charging()
        else:
            if self.player.is_charging:
                if self.player.charge_sound_playing: self.channel_player_charge.stop()
                self.player.stop_charging()
                self.channel_player_actions.play(self.snd_dash)

    def start_fade(self, to_black, callback=None):
        self.fading_to_black = to_black
        self.fading_from_black = not to_black
        self.fade_alpha = 0 if to_black else 255
        self.fade_callback = callback
        if to_black: self.channel_bg_music.fadeout(500)

    def show_demo_end_message(self):
        self.ui.show_demo_end_screen()

    def update(self, dt):
        if self.ui.showing_intro:
            self.ui.update_intro(dt)
            return
        if self.game_over:
             if pygame.key.get_pressed()[pygame.K_RETURN]: self.reset_game()
             return

        if self.fading_to_black or self.fading_from_black:
            speed = 150
            if self.fading_to_black:
                self.fade_alpha = min(255, self.fade_alpha + speed * dt)
                if self.fade_alpha >= 255:
                    self.fading_to_black = False
                    if self.fade_callback: self.fade_callback()
            else:
                self.fade_alpha = max(0, self.fade_alpha - speed * dt)
                if self.fade_alpha <= 0:
                    self.fading_from_black = False
                    if self.fade_callback: self.fade_callback()
            return
        
        if not self.paused:
            if not self.ui.showing_intro and not self.boss_defeated:
                new_boss_visible = self.boss and self.boss.alive() and self.camera.is_in_camera_view(self.boss.rect)
                if new_boss_visible != self.boss_visible:
                    self.boss_visible = new_boss_visible
                    self.channel_bg_music.fadeout(500)
                    next_music = self.boss_music if new_boss_visible else self.bg_music
                    self.channel_bg_music.play(next_music, -1)
                elif not self.channel_bg_music.get_busy():
                    self.channel_bg_music.play(self.bg_music, -1)
            
            self.player.update(self.map_loader.obstacles, self.map_loader.platforms, self.map_loader.falling_tiles, self.map_loader.map_width, self.map_loader.map_height, dt)
            self.update_breakable_tiles_collidable_state()
            self.enemies.update(self.map_loader.obstacles, self.map_loader.platforms, self.player, self.map_loader.map_width, self.map_loader.map_height, dt)
            for enemy in self.enemies:
                if hasattr(enemy, 'projectiles'): self.enemy_projectiles.add(enemy.projectiles.sprites())
            
            for enemy in self.enemies.copy():
                if not enemy.alive():
                    self.enemies.remove(enemy)
                    if enemy is self.boss:
                        self.boss = None
                        self.boss_defeated = True
                        self.start_fade(True, self.show_demo_end_message)

            self.enemy_projectiles.update(self.map_loader.obstacles, self.player, dt)
            
            self.map_loader.falling_tiles.update(dt)
            self.map_loader.breakable_tiles.update(dt)

            enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
            for enemy in enemy_hits:
                if self.player.dashing:
                    enemy.take_damage(self.player.dash_damage, 1 if enemy.rect.centerx > self.player.rect.centerx else -1)
                elif hasattr(enemy, 'health') and enemy.health > 0:
                    self.player.take_damage(enemy.damage, 1 if self.player.rect.centerx > enemy.rect.centerx else -1)

            vine_hits = pygame.sprite.groupcollide(self.vines, self.enemies, False, False)
            for vine, enemies_hit in vine_hits.items():
                for enemy in enemies_hit:
                    enemy.take_damage(1, 1 if enemy.rect.centerx > vine.rect.centerx else -1)

            healing_hits = pygame.sprite.spritecollide(self.player, self.map_loader.healing_tiles, True)
            for tile in healing_hits:
                self.player.heal(self.player.max_health)
                self.channel_healing.play(self.snd_heal)
                self.ui.create_floating_text("HP FULL!", self.camera.apply(self.player.rect).midtop, (0, 255, 0))

            self.vines.update(dt)
            
            if self.player.current_health <= 0 and not self.game_over:
                self.game_over = True
                self.ui.game_over = True
                self.channel_bg_music.stop()

            coins_hit = pygame.sprite.spritecollide(self.player, self.map_loader.collectables, True)
            if coins_hit:
                self.ui.coins_collected += len(coins_hit)
                self.player.dash_damage += len(coins_hit)
                self.ui.show_coin_counter()
                self.channel_collectables.play(self.snd_coin)
                for coin in coins_hit:
                    self.ui.create_floating_text("+1", self.camera.apply(coin.rect).center)
                    self.ui.create_floating_text("DMG UP!", self.camera.apply(self.player.rect).midtop, (255, 215, 0))

            self.camera.update(self.player, dt)
            self.ui.update(dt, self.paused)

    def render(self):
        self.screen.fill((77, 9, 179))
        
        if not self.ui.showing_intro and not self.ui.showing_demo_end:
            self.map_loader.draw_parallax_background(self.screen, self.camera.current_x, self.camera.current_y)
            
            self.map_loader.draw_static_tiles(self.screen, self.camera)
            self.map_loader.draw_dynamic_tiles(self.screen, self.camera)
            
            for group in [self.vines, self.enemy_projectiles, self.enemies]:
                for sprite in group:
                    self.screen.blit(sprite.image, self.camera.apply(sprite.rect))

            for enemy in self.enemies:
                if not isinstance(enemy, EtherJumperBoss): enemy.draw_health_bar(self.screen, self.camera)
            
            if not self.game_over:
                self.screen.blit(self.player.image, self.camera.apply(self.player.rect))
                self.player.draw_charge_bar(self.screen, self.camera)

        self.ui.draw(self.screen)

        if not self.game_over and self.boss and self.boss.alive():
            self.boss.draw_health_bar(self.screen, self.camera)

        if self.ui.showing_intro: self.ui.draw_intro(self.screen)
        if self.ui.showing_demo_end: self.ui.draw_demo_end_screen(self.screen)

        if self.fading_to_black or self.fading_from_black:
            fade_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self.fade_alpha)))
            self.screen.blit(fade_surf, (0,0))