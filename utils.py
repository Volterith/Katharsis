# MultipleFiles/utils.py
import os
import sys
import pygame

def get_resource_path(*path):
    """Получает правильный путь к ресурсам для собранного и несобранного приложения"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, *path)

def load_font(name, size):
    try:
        # Проверяем, инициализирован ли модуль шрифтов
        if not pygame.font.get_init():
            pygame.font.init()
            
        font_path = get_resource_path("Fonts", name)
        return pygame.font.Font(font_path, size)
    except Exception as e:
        print(f"Не удалось загрузить шрифт {name}: {e}")
        # Проверяем снова перед использованием SysFont
        if not pygame.font.get_init():
            pygame.font.init()
        return pygame.font.SysFont("Arial", size)

def load_image(name):
    try:
        image_path = get_resource_path("Sprites", name)
        image = pygame.image.load(image_path)
        return image
    except Exception as e:
        print(f"Не удалось загрузить изображение {name}: {e}")
        placeholder = pygame.Surface((132, 86))
        placeholder.fill((24, 89, 133)) # BLUE
        pygame.draw.rect(placeholder, (255, 255, 255), (0, 0, 132, 86), 2) # WHITE
        return placeholder