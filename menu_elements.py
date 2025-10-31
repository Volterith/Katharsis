# MultipleFiles/menu_elements.py
import pygame
import math
from pygame.locals import *
from utils import load_font

# Цвета
WHITE = (255, 255, 255)
DARK_GREY = (40, 40, 40)
RED = (80, 0, 0)
BLUE = (24, 89, 133)
GREEN = (21, 117, 62)

# Шрифты
font_medium = load_font("munro.otf", 24)
font_small = load_font("munro.otf", 16)

class PixelButton:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.is_selected = False
        self.pulse_time = 0
        self.action = action
        
    def update(self, dt):
        self.pulse_time += dt * 6
        
    def draw(self, surface, offset_y=0):
        current_rect = self.rect.move(0, offset_y)
        
        pulse = 0
        if self.is_selected:
            pulse = int(5 * math.sin(self.pulse_time))
        
        button_color = self.hover_color if (self.is_hovered or self.is_selected) else self.color
        pygame.draw.rect(surface, button_color, current_rect.inflate(pulse, pulse), 0, 3)
        
        border_color = WHITE if (self.is_hovered or self.is_selected) else DARK_GREY
        pygame.draw.rect(surface, border_color, current_rect.inflate(pulse, pulse), 2, 3)
        
        text_surf = font_medium.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=current_rect.center)
        surface.blit(text_surf, text_rect)
        
    def set_hover(self, hover):
        self.is_hovered = hover
        
    def set_selected(self, selected):
        self.is_selected = selected

    # ИЗМЕНЕНИЕ: Сигнатура изменена для приема координат мыши
    def handle_event(self, event, offset_y=0, logical_mouse_pos=None):
        if logical_mouse_pos is None:
            return None
            
        current_rect = self.rect.move(0, offset_y)
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if current_rect.collidepoint(logical_mouse_pos):
                return self.action
        return None

class VolumeSlider:
    def __init__(self, x, y, width, height, label, initial_value, min_val=0.0, max_val=1.0):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = initial_value
        self.min_val = min_val
        self.max_val = max_val
        self.dragging = False
        self.is_selected = False
        self.pulse_time = 0

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = max(self.min_val, min(self.max_val, value))

    # ИЗМЕНЕНИЕ: Сигнатура изменена для приема координат мыши
    def handle_event(self, event, offset_y=0, logical_mouse_pos=None):
        if logical_mouse_pos is None:
            return False
            
        current_rect = self.rect.move(0, offset_y)
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if current_rect.collidepoint(logical_mouse_pos):
                self.dragging = True
                self.update_from_mouse(logical_mouse_pos[0], current_rect)
                return True
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == MOUSEMOTION:
            if self.dragging:
                self.update_from_mouse(logical_mouse_pos[0], current_rect)
                return True
        return False

    def update_from_mouse(self, mouse_x, current_rect):
        relative_x = mouse_x - current_rect.x
        self.value = self.min_val + (relative_x / current_rect.width) * (self.max_val - self.min_val)
        self.value = max(self.min_val, min(self.max_val, self.value))

    def update(self, dt):
        self.pulse_time += dt * 6

    def draw(self, surface, offset_y=0):
        current_rect = self.rect.move(0, offset_y)
        
        pulse = 0
        if self.is_selected:
            pulse = int(3 * math.sin(self.pulse_time))

        pygame.draw.rect(surface, DARK_GREY, current_rect.inflate(pulse, pulse), 0, 3)
        pygame.draw.rect(surface, WHITE, current_rect.inflate(pulse, pulse), 2, 3)

        slider_x = current_rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * current_rect.width)
        pygame.draw.circle(surface, GREEN, (slider_x, current_rect.centery), current_rect.height // 2 - 2 + pulse)

        label_surf = font_medium.render(f"{self.label}: {int(self.value * 100)}%", True, WHITE)
        label_rect = label_surf.get_rect(midright=(current_rect.x - 10, current_rect.centery))
        surface.blit(label_surf, label_rect)
    
    def set_selected(self, selected):
        self.is_selected = selected

class KeybindButton:
    def __init__(self, x, y, width, height, label, current_key_code, action_name):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.current_key_code = current_key_code
        self.action_name = action_name
        self.waiting_for_input = False
        self.is_selected = False
        self.pulse_time = 0

    def get_key_name(self):
        return pygame.key.name(self.current_key_code).upper()

    # ИЗМЕНЕНИЕ: Сигнатура изменена для приема координат мыши
    def handle_event(self, event, offset_y=0, logical_mouse_pos=None):
        if logical_mouse_pos is None and event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
             return False

        current_rect = self.rect.move(0, offset_y)
        if self.waiting_for_input:
            if event.type == KEYDOWN:
                if event.key != K_RETURN:
                    self.current_key_code = event.key
                    self.waiting_for_input = False
                    return True
            elif event.type == MOUSEBUTTONDOWN and not current_rect.collidepoint(logical_mouse_pos):
                self.waiting_for_input = False
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            if current_rect.collidepoint(logical_mouse_pos):
                self.waiting_for_input = True
                return False
        return False

    def update(self, dt):
        self.pulse_time += dt * 6

    def draw(self, surface, offset_y=0):
        current_rect = self.rect.move(0, offset_y)
        
        pulse = 0
        if self.is_selected or self.waiting_for_input:
            pulse = int(3 * math.sin(self.pulse_time))

        button_color = BLUE if not self.waiting_for_input else RED
        pygame.draw.rect(surface, button_color, current_rect.inflate(pulse, pulse), 0, 3)
        pygame.draw.rect(surface, WHITE, current_rect.inflate(pulse, pulse), 2, 3)

        label_surf = font_medium.render(self.label, True, WHITE)
        label_rect = label_surf.get_rect(midright=(current_rect.x - 10, current_rect.centery))
        surface.blit(label_surf, label_rect)

        key_name = "Нажмите клавишу..." if self.waiting_for_input else self.get_key_name()
        key_surf = font_medium.render(key_name, True, WHITE)
        key_rect = key_surf.get_rect(center=(current_rect.centerx, current_rect.centery))
        surface.blit(key_surf, key_rect)
    
    def set_selected(self, selected):
        self.is_selected = selected