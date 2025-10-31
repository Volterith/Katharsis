# MultipleFiles/menu_screens.py
import pygame
import random
from pygame.locals import *
from utils import load_font, get_resource_path, load_image
from menu_elements import PixelButton, VolumeSlider, KeybindButton
from settings_manager import SettingsManager

# Цвета
WHITE = (255, 255, 255)
DARK_GREY = (40, 40, 40)
BLUE = (24, 89, 133)
GREEN = (21, 117, 62)
RED = (122, 34, 28)

# Шрифты
font_large = load_font("munro.otf", 32)
font_medium = load_font("munro.otf", 24)
font_small = load_font("munro.otf", 16)

class RainEffect:
    def __init__(self, surface):
        self.surface = surface
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()
        self.particles = []
        for _ in range(150):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            speed = random.randint(200, 400) # Скорость в пикселях/сек
            self.particles.append([x, y, speed])

        self.thunder_timer = random.uniform(10, 25)
        self.flash_alpha = 0
        try:
            self.snd_thunder = pygame.mixer.Sound(get_resource_path("Sounds", "thunder.wav"))
        except pygame.error:
            self.snd_thunder = None
            print("Warning: 'Sounds/thunder.wav' not found.")

    def update(self, dt):
        for p in self.particles:
            p[1] += p[2] * dt
            p[0] -= (p[2] // 2) * dt
            if p[1] > self.height:
                p[1] = random.randint(-20, -5)
                p[0] = random.randint(0, self.width)
            if p[0] < 0:
                p[0] = self.width
        
        self.thunder_timer -= dt
        if self.thunder_timer <= 0:
            self.thunder_timer = random.uniform(10, 25)
            self.flash_alpha = 255
            if self.snd_thunder:
                self.snd_thunder.set_volume(0.7)
                self.snd_thunder.play()

        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - (255 / 0.5) * dt)

    def draw(self, surface):
        for p in self.particles:
            length = p[2] / 20.0
            start_pos = (p[0], p[1])
            end_pos = (p[0] - length/2, p[1] + length * 2)
            pygame.draw.line(surface, (130, 150, 180), start_pos, end_pos, 2)
            
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, self.flash_alpha))
            surface.blit(flash_surface, (0, 0))

class TextElement:
    def __init__(self, x_center, y, text, font, color=WHITE):
        self.font = font
        self.original_text = text
        self.text_surf = self.font.render(text, True, color)
        self.rect = self.text_surf.get_rect(center=(x_center, y))
        self.is_selected = False

    def draw(self, surface, offset_y=0):
        current_rect = self.rect.move(0, offset_y)
        surface.blit(self.text_surf, current_rect)

    def update(self, dt): pass
    def set_selected(self, selected): pass
    def update_text(self, new_text, center_x):
        self.text_surf = self.font.render(new_text, True, WHITE)
        self.rect = self.text_surf.get_rect(center=(center_x, self.rect.centery))


class BaseMenuScreen:
    def __init__(self, screen, settings_manager, background_effect, logo_image=None):
        self.screen = screen
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        self.settings_manager = settings_manager
        self.background_effect = background_effect
        self.logo_image = logo_image
        self.elements = []
        self.selected_element_index = 0
        self.scroll_offset_y = 0
        self.max_scroll_offset_y = 0
        self.scroll_speed = 20
        self.fixed_elements = []

    # ИЗМЕНЕНИЕ: Сигнатура изменена для приема координат мыши
    def handle_input(self, event, logical_mouse_pos=None):
        if event.type == KEYDOWN:
            interactive_elements = [e for e in self.elements + self.fixed_elements if not isinstance(e, TextElement)]
            if interactive_elements:
                current_interactive_index = -1
                if 0 <= self.selected_element_index < len(self.elements + self.fixed_elements):
                    selected_obj = (self.elements + self.fixed_elements)[self.selected_element_index]
                    if selected_obj in interactive_elements:
                        current_interactive_index = interactive_elements.index(selected_obj)

                if event.key == K_DOWN:
                    new_interactive_index = (current_interactive_index + 1) % len(interactive_elements)
                elif event.key == K_UP:
                    new_interactive_index = (current_interactive_index - 1 + len(interactive_elements)) % len(interactive_elements)
                else:
                    return None
                
                new_selected_obj = interactive_elements[new_interactive_index]
                self.selected_element_index = (self.elements + self.fixed_elements).index(new_selected_obj)
                self._adjust_scroll()

        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 4: self.scroll_offset_y = max(0, self.scroll_offset_y - self.scroll_speed)
            elif event.button == 5: self.scroll_offset_y = min(self.max_scroll_offset_y, self.scroll_offset_y + self.scroll_speed)
        return None

    # ИЗМЕНЕНИЕ: Сигнатура изменена для приема координат мыши
    def update(self, dt, logical_mouse_pos=None):
        mouse_pos = logical_mouse_pos or (0,0)
        all_elements = self.elements + self.fixed_elements
        for i, element in enumerate(all_elements):
            element.update(dt)
            is_interactive = not isinstance(element, TextElement)
            if is_interactive:
                element.set_selected(i == self.selected_element_index)
            
            is_fixed = element in self.fixed_elements
            offset = 0 if is_fixed else -self.scroll_offset_y
            
            if isinstance(element, PixelButton):
                 element.set_hover(element.rect.move(0, offset).collidepoint(mouse_pos))

    def draw(self, dt, show_logo=True):
        if self.background_effect:
            self.background_effect.update(dt)
            self.background_effect.draw(self.screen)
        
        if show_logo and self.logo_image:
            logo_rect = self.logo_image.get_rect(center=(self.width//2, 150))
            self.screen.blit(self.logo_image, logo_rect)

        for element in self.elements: element.draw(self.screen, -self.scroll_offset_y)
        for element in self.fixed_elements: element.draw(self.screen, 0)
        self._draw_scroll_bar(self.screen)
        
    def _calculate_max_scroll(self):
        if not self.elements:
            self.max_scroll_offset_y = 0
            return
        
        content_top = self.elements[0].rect.top
        content_bottom = self.elements[-1].rect.bottom
        content_height = content_bottom - content_top
        
        visible_area_height = self.height - 100 

        if content_height > visible_area_height:
            self.max_scroll_offset_y = content_height - visible_area_height
        else:
            self.max_scroll_offset_y = 0
        
        self.scroll_offset_y = min(self.scroll_offset_y, self.max_scroll_offset_y)

    def _adjust_scroll(self):
        if not self.elements or self.selected_element_index >= len(self.elements):
            return

        selected_element = self.elements[self.selected_element_index]
        if isinstance(selected_element, TextElement): return

        element_top = selected_element.rect.top
        element_bottom = selected_element.rect.bottom
        
        visible_area_top = 50 
        visible_area_bottom = self.height - 50

        if element_top - self.scroll_offset_y < visible_area_top:
            self.scroll_offset_y = element_top - visible_area_top
        elif element_bottom - self.scroll_offset_y > visible_area_bottom:
            self.scroll_offset_y = element_bottom - visible_area_bottom

        self.scroll_offset_y = max(0, min(self.scroll_offset_y, self.max_scroll_offset_y))

    def _draw_scroll_bar(self, surface):
        if self.max_scroll_offset_y > 0:
            bar_x = self.width - 20; bar_y_offset = 50
            bar_height = self.height - 100; bar_width = 10
            pygame.draw.rect(surface, DARK_GREY, (bar_x, bar_y_offset, bar_width, bar_height), 0, 5)
            
            content_height = self.elements[-1].rect.bottom - self.elements[0].rect.top
            visible_ratio = (self.height - 100) / content_height
            if visible_ratio < 1:
                slider_height = bar_height * visible_ratio
                scroll_ratio = self.scroll_offset_y / self.max_scroll_offset_y
                slider_y = bar_y_offset + scroll_ratio * (bar_height - slider_height)
                pygame.draw.rect(surface, GREEN, (bar_x, slider_y, bar_width, slider_height), 0, 5)

class MainMenuScreen(BaseMenuScreen):
    def __init__(self, screen, settings_manager, background_effect, logo_image):
        super().__init__(screen, settings_manager, background_effect, logo_image)
        center_x = self.width // 2
        self.elements = [
            PixelButton(center_x - 100, 250, 200, 40, "ИГРАТЬ", GREEN, (65, 148, 65), action="play"),
            PixelButton(center_x - 100, 300, 200, 40, "НАСТРОЙКИ", BLUE, (62, 104, 148), action="options"),
            PixelButton(center_x - 100, 350, 200, 40, "АВТОРЫ", BLUE, (62, 104, 148), action="authors"),
            PixelButton(center_x - 100, 400, 200, 40, "ВЫХОД", RED, (122, 34, 28), action="exit")
        ]
        self.selected_element_index = 0
        if self.elements: self.elements[0].set_selected(True)

    def handle_input(self, event, logical_mouse_pos=None):
        super().handle_input(event, logical_mouse_pos)
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.elements):
                if action := button.handle_event(event, logical_mouse_pos=logical_mouse_pos):
                    self.selected_element_index = i
                    return action
        if event.type == KEYDOWN and event.key == K_RETURN:
            if 0 <= self.selected_element_index < len(self.elements):
                element = self.elements[self.selected_element_index]
                if hasattr(element, 'action'): return element.action
        return None

    def draw(self, dt):
        super().draw(dt, show_logo=True)

class OptionsScreen(BaseMenuScreen):
    def __init__(self, screen, settings_manager, background_effect):
        self.fps_options = ["60", "120", "144", "Unlimited"]
        self.aspect_ratio_options = ["4:3", "16:9", "16:10", "3:2"]
        self.window_mode_options = ["windowed", "fullscreen", "borderless"]
        self.window_mode_text_map = {
            "windowed": "Оконный",
            "fullscreen": "Полный экран",
            "borderless": "Без рамки"
        }
        self.window_scale_options = ["1", "2", "3", "4"]
        super().__init__(screen, settings_manager, background_effect, None)
        self._create_elements()
        self.selected_element_index = 1 
        if self.elements: self.elements[self.selected_element_index].set_selected(True)
        self._calculate_max_scroll()

    def _create_elements(self):
        self.elements = []
        center_x = self.width // 2
        title = TextElement(center_x, 80, "НАСТРОЙКИ", font_large)
        self.elements.append(title)
        y_start = 150
        self.music_slider = VolumeSlider(center_x + 20, y_start, 200, 20, "Музыка", self.settings_manager.get_music_volume())
        self.sfx_slider = VolumeSlider(center_x + 20, y_start + 50, 200, 20, "Звуки", self.settings_manager.get_sfx_volume())
        self.elements.extend([self.music_slider, self.sfx_slider])
        
        y_offset = y_start + 100
        for action, key_code in self.settings_manager.get_controls().items():
            kb = KeybindButton(center_x + 20, y_offset, 200, 30, action.replace('_', ' ').title(), key_code, action)
            self.elements.append(kb); y_offset += 40

        particles_text = f"Частицы: {'ВКЛ' if self.settings_manager.get_particles_enabled() else 'ВЫКЛ'}"
        self.particles_button = PixelButton(center_x - 100, y_offset, 200, 40, particles_text, BLUE, (62, 104, 148), action="toggle_particles")
        y_offset += 50
        self.elements.append(self.particles_button)

        current_fps = self.settings_manager.get_max_fps()
        fps_text = f"Max FPS: {current_fps if current_fps != 0 else 'Unlimited'}"
        self.fps_button = PixelButton(center_x - 100, y_offset, 200, 40, fps_text, BLUE, (62, 104, 148), action="toggle_fps")
        y_offset += 50
        self.elements.append(self.fps_button)

        aspect_ratio_text = f"Соотношение: {self.settings_manager.get_aspect_ratio()}"
        self.aspect_ratio_button = PixelButton(center_x - 100, y_offset, 200, 40, aspect_ratio_text, BLUE, (62, 104, 148), action="toggle_aspect_ratio")
        y_offset += 50
        self.elements.append(self.aspect_ratio_button)

        current_scale = self.settings_manager.get_window_scale()
        window_scale_text = f"Масштаб окна: x{current_scale}"
        self.window_scale_button = PixelButton(center_x - 100, y_offset, 200, 40, window_scale_text, BLUE, (62, 104, 148), action="toggle_window_scale")
        y_offset += 50
        self.elements.append(self.window_scale_button)
        
        current_mode = self.settings_manager.get_window_mode()
        window_mode_text = f"Окно: {self.window_mode_text_map.get(current_mode, 'Оконный')}"
        self.window_mode_button = PixelButton(center_x - 100, y_offset, 200, 40, window_mode_text, BLUE, (62, 104, 148), action="toggle_window_mode")
        y_offset += 40
        self.elements.append(self.window_mode_button)

        self.restart_label = TextElement(center_x, y_offset + 5, "(требуется перезапуск)", font_small, (200, 200, 200))
        y_offset += 25
        self.elements.append(self.restart_label)

        self.back_button = PixelButton(center_x - 100, y_offset, 200, 40, "НАЗАД", BLUE, (62, 104, 148), action="back")
        self.elements.append(self.back_button)

    def handle_input(self, event, logical_mouse_pos=None):
        super().handle_input(event, logical_mouse_pos)
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and logical_mouse_pos:
            for i, element in enumerate(self.elements):
                if not isinstance(element, TextElement) and element.rect.move(0, -self.scroll_offset_y).collidepoint(logical_mouse_pos):
                    self.selected_element_index = i; break
        
        for element in self.elements:
            if hasattr(element, 'handle_event') and element.handle_event(event, logical_mouse_pos=logical_mouse_pos, offset_y=-self.scroll_offset_y):
                if isinstance(element, VolumeSlider):
                    vol = element.get_value()
                    if "Музыка" in element.label: pygame.mixer.music.set_volume(vol); self.settings_manager.set_music_volume(vol)
                    elif "Звуки" in element.label: self.settings_manager.set_sfx_volume(vol)
                elif isinstance(element, KeybindButton) and not element.waiting_for_input:
                    self.settings_manager.set_control(element.action_name, element.current_key_code)

        if 0 <= self.selected_element_index < len(self.elements):
            selected_element = self.elements[self.selected_element_index]
            action = None
            if event.type == MOUSEBUTTONDOWN and event.button == 1 and logical_mouse_pos:
                if isinstance(selected_element, PixelButton) and selected_element.rect.move(0, -self.scroll_offset_y).collidepoint(logical_mouse_pos):
                    action = getattr(selected_element, 'action', None)
            elif event.type == KEYDOWN and event.key == K_RETURN:
                if isinstance(selected_element, PixelButton): action = getattr(selected_element, 'action', None)
                elif isinstance(selected_element, KeybindButton): selected_element.waiting_for_input = True
            
            if action:
                if action == "back": return "back"
                if action == "toggle_particles":
                    new_state = not self.settings_manager.get_particles_enabled()
                    self.settings_manager.set_particles_enabled(new_state)
                    self.particles_button.text = f"Частицы: {'ВКЛ' if new_state else 'ВЫКЛ'}"
                
                if action == "toggle_window_mode":
                    current_mode = self.settings_manager.get_window_mode()
                    try:
                        current_index = self.window_mode_options.index(current_mode)
                        next_index = (current_index + 1) % len(self.window_mode_options)
                    except ValueError:
                        next_index = 0
                    
                    new_mode = self.window_mode_options[next_index]
                    self.settings_manager.set_window_mode(new_mode)
                    self.window_mode_button.text = f"Окно: {self.window_mode_text_map.get(new_mode, 'Оконный')}"

                if action == "toggle_window_scale":
                    current_scale_str = str(self.settings_manager.get_window_scale())
                    try:
                        current_index = self.window_scale_options.index(current_scale_str)
                        next_index = (current_index + 1) % len(self.window_scale_options)
                    except ValueError:
                        next_index = 1 
                    
                    new_scale_str = self.window_scale_options[next_index]
                    self.settings_manager.set_window_scale(new_scale_str)
                    self.window_scale_button.text = f"Масштаб окна: x{new_scale_str}"

                if action == "toggle_aspect_ratio":
                    current_ratio = self.settings_manager.get_aspect_ratio()
                    try:
                        current_index = self.aspect_ratio_options.index(current_ratio)
                        next_index = (current_index + 1) % len(self.aspect_ratio_options)
                    except ValueError:
                        next_index = 0
                    
                    new_ratio = self.aspect_ratio_options[next_index]
                    self.settings_manager.set_aspect_ratio(new_ratio)
                    self.aspect_ratio_button.text = f"Соотношение: {new_ratio}"

                if action == "toggle_fps":
                    current_fps_str = str(self.settings_manager.get_max_fps() if self.settings_manager.get_max_fps() != 0 else "Unlimited")
                    try:
                        current_index = self.fps_options.index(current_fps_str)
                        next_index = (current_index + 1) % len(self.fps_options)
                    except ValueError:
                        next_index = 0
                    
                    new_fps_str = self.fps_options[next_index]
                    self.settings_manager.set_max_fps(new_fps_str)
                    
                    new_fps_val = self.settings_manager.get_max_fps()
                    self.fps_button.text = f"Max FPS: {new_fps_val if new_fps_val != 0 else 'Unlimited'}"

            if event.type == KEYDOWN and isinstance(selected_element, VolumeSlider):
                if event.key == K_LEFT: selected_element.set_value(selected_element.get_value() - 0.05)
                elif event.key == K_RIGHT: selected_element.set_value(selected_element.get_value() + 0.05)
                vol = selected_element.get_value()
                if "Музыка" in selected_element.label: pygame.mixer.music.set_volume(vol); self.settings_manager.set_music_volume(vol)
                elif "Звуки" in selected_element.label: self.settings_manager.set_sfx_volume(vol)
        return None

    def draw(self, dt):
        super().draw(dt, show_logo=False)

class AuthorsScreen(BaseMenuScreen):
    def __init__(self, screen, settings_manager, background_effect):
        super().__init__(screen, settings_manager, background_effect, None)
        center_x = self.width // 2
        self.authors_text_lines = [
            "РАЗРАБОТЧИКИ:", "", "ПРОГРАММИСТ: Volterith", "ХУДОЖНИК: ItsFrancesco78",
            "МУЗЫКАНТ: Lisik_Rin, Daniil Vlasenko", "", "#Game-Jam: 2025 Summer"
        ]
        self.back_button = PixelButton(center_x - 100, 380, 200, 40, "НАЗАД", BLUE, (62, 104, 148), action="back")
        self.fixed_elements = [self.back_button]
        self.selected_element_index = 0
        if self.fixed_elements: self.fixed_elements[0].set_selected(True)

    def handle_input(self, event, logical_mouse_pos=None):
        if (event.type == MOUSEBUTTONDOWN and event.button == 1 and self.back_button.handle_event(event, logical_mouse_pos=logical_mouse_pos) == "back") or \
           (event.type == KEYDOWN and (event.key == K_RETURN or event.key == K_ESCAPE)):
            return "back"
        return None

    def draw(self, dt):
        super().draw(dt, show_logo=False)
        center_x = self.width // 2
        title = font_large.render("АВТОРЫ", True, WHITE)
        self.screen.blit(title, (center_x - title.get_width()//2, 80))
        for i, line in enumerate(self.authors_text_lines):
            text_surf = font_medium.render(line, True, WHITE)
            text_rect = text_surf.get_rect(center=(center_x, 150 + i * 30))
            self.screen.blit(text_surf, text_rect)
        self.back_button.draw(self.screen, 0)

class PauseMenu(BaseMenuScreen):
    def __init__(self, screen, settings_manager, game_snapshot):
        super().__init__(screen, settings_manager, None, None) 
        self.game_snapshot = game_snapshot
        center_x = self.width // 2
        self.elements = [
            PixelButton(center_x - 100, 180, 200, 40, "ПРОДОЛЖИТЬ", GREEN, (65, 148, 65), action="continue"),
            PixelButton(center_x - 100, 240, 200, 40, "В МЕНЮ", BLUE, (62, 104, 148), action="main_menu")
        ]
        self.selected_element_index = 0
        if self.elements: self.elements[0].set_selected(True)

    def handle_input(self, event, logical_mouse_pos=None):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.elements):
                if action := button.handle_event(event, logical_mouse_pos=logical_mouse_pos):
                    self.selected_element_index = i
                    return action
        if event.type == KEYDOWN:
            if event.key == K_DOWN: self.selected_element_index = (self.selected_element_index + 1) % len(self.elements)
            elif event.key == K_UP: self.selected_element_index = (self.selected_element_index - 1 + len(self.elements)) % len(self.elements)
            elif event.key == K_RETURN: return self.elements[self.selected_element_index].action
            elif event.key == K_ESCAPE: return "continue"
        return None
        
    def update(self, dt=0, logical_mouse_pos=None):
        super().update(dt, logical_mouse_pos)

    def draw(self, dt=0):
        if self.game_snapshot:
            self.screen.blit(self.game_snapshot, (0, 0))
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 200))
        self.screen.blit(overlay, (0, 0))
        pause_text = font_large.render("ПАУЗА", True, WHITE)
        self.screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, 100))
        for element in self.elements:
            element.draw(self.screen)