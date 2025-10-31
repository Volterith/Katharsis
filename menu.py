# MultipleFiles/menu.py
import pygame
import sys
import os
import random
import math
from pygame.locals import *

# Импортируем игру напрямую
from main import run_game

# Импортируем новые модули
from menu_elements import PixelButton, VolumeSlider, KeybindButton
from menu_screens import MainMenuScreen, OptionsScreen, AuthorsScreen, PauseMenu
from settings_manager import SettingsManager
from utils import get_resource_path, load_font, load_image

# Инициализация Pygame
pygame.init()
pygame.font.init()

# Константы
WIDTH, HEIGHT = 640, 480
FPS = 60
FADE_SPEED = 8

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Создание окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Katharsis")
clock = pygame.time.Clock()

# Логотип
logo_image = load_image("logo.png")

# Класс для fade-эффекта
class FadeEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.alpha = 0
        self.fade_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.fade_surface.fill((0, 0, 0, 0))
        self.zooming = False
        self.zoom_scale = 1.0
        self.zoom_speed = 0.05
    
    def start_fade(self):
        self.alpha = 0
        self.zooming = True
        self.zoom_scale = 1.0
    
    def update(self):
        if self.zooming:
            self.alpha = min(self.alpha + FADE_SPEED, 255)
            self.zoom_scale += self.zoom_speed
            if self.alpha >= 255:
                self.zooming = False
                return True
        return False
    
    def draw(self, surface):
        self.fade_surface.fill((0, 0, 0, self.alpha))
        surface.blit(self.fade_surface, (0, 0))
    
    def apply_zoom(self, surface):
        if self.zooming:
            scaled_surface = pygame.transform.scale(
                surface, 
                (int(self.width * self.zoom_scale), int(self.height * self.zoom_scale)))
            screen.blit(
                scaled_surface, 
                (self.width//2 - scaled_surface.get_width()//2, self.height//2 - scaled_surface.get_height()//2))
            return True
        return False

# Класс для эффекта дождя
class RainEffect:
    def __init__(self, width, height, num_drops=100):
        self.width = width
        self.height = height
        self.drops = []
        self.num_drops = num_drops
        self.create_drops()

    def create_drops(self):
        for _ in range(self.num_drops):
            self.drops.append(self.create_single_drop())

    def create_single_drop(self):
        x = random.randint(0, self.width)
        y = random.randint(-self.height, 0)
        length = random.randint(15, 20)
        speed = random.randint(5, 10)
        return {'x': x, 'y': y, 'length': length, 'speed': speed}

    def update(self):
        for drop in self.drops:
            drop['y'] += drop['speed']
            if drop['y'] > self.height:
                drop.update(self.create_single_drop())
                drop['y'] = random.randint(-50, -10)

    def draw(self, surface):
        for drop in self.drops:
            pygame.draw.line(surface, (150, 200, 255, 150), (drop['x'], drop['y']), 
                             (drop['x'], drop['y'] + drop['length']), 2)

# Основной игровой цикл меню
def main():
    settings_manager = SettingsManager()
    
    rain_effect = RainEffect(WIDTH, HEIGHT)
    fade_effect = FadeEffect(WIDTH, HEIGHT)

    pygame.mixer.music.load(get_resource_path("Music", "menu.mp3"))
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(settings_manager.get_music_volume())

    main_menu_screen = MainMenuScreen(screen, settings_manager, rain_effect, logo_image)
    options_screen = OptionsScreen(screen, settings_manager, rain_effect)
    authors_screen = AuthorsScreen(screen, settings_manager, rain_effect)
    
    current_screen = main_menu_screen

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            action = current_screen.handle_input(event)

            if current_screen == main_menu_screen:
                if action == "play":
                    pygame.mixer.music.stop()
                    fade_effect.start_fade()
                    while not fade_effect.update():
                        main_menu_screen.draw()
                        fade_effect.draw(screen)
                        pygame.display.flip()
                        clock.tick(FPS)
                    
                    # ПЕРЕДАЕМ ВСЕ НАСТРОЙКИ, ВКЛЮЧАЯ ЧАСТИЦЫ
                    should_return_to_menu = run_game(
                        screen, 
                        PauseMenu(screen, settings_manager, screen.copy()),
                        settings_manager.get_music_volume(), 
                        settings_manager.get_sfx_volume(), 
                        settings_manager.get_controls(),
                        settings_manager.get_particles_enabled() # <--- НОВАЯ СТРОКА
                    )
                    if not should_return_to_menu:
                        running = False
                    
                    fade_effect.alpha = 0
                    pygame.mixer.music.play(-1)
                    pygame.mixer.music.set_volume(settings_manager.get_music_volume())
                    current_screen = main_menu_screen
                elif action == "options":
                    current_screen = options_screen
                elif action == "authors":
                    current_screen = authors_screen
                elif action == "exit":
                    running = False
            elif current_screen == options_screen:
                if action == "back":
                    current_screen = main_menu_screen
            elif current_screen == authors_screen:
                if action == "back":
                    current_screen = main_menu_screen
            
        current_screen.update()
        current_screen.draw()
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()