import pygame
import sys
import random
from menu_screens import MainMenuScreen, OptionsScreen, AuthorsScreen, PauseMenu
from settings_manager import SettingsManager
from utils import load_image, get_resource_path
from game import Game

# Константы
RESOLUTIONS = {
    "4:3": (640, 480),
    "16:9": (854, 480),
    "16:10": (768, 480),
    "3:2": (720, 480)
}

# Эффект дождя для меню
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

class App:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()

        self.settings_manager = SettingsManager()
        
        self.logical_size = RESOLUTIONS.get(self.settings_manager.get_aspect_ratio(), (640, 480))
        
        window_mode = self.settings_manager.get_window_mode()
        window_scale = self.settings_manager.get_window_scale()
        
        display_flags = 0 
        
        if window_mode == 'fullscreen':
            display_flags |= pygame.FULLSCREEN
            self.display_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        elif window_mode == 'borderless':
            display_flags |= pygame.NOFRAME
            self.display_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        else: # windowed
            self.display_size = (self.logical_size[0] * window_scale, self.logical_size[1] * window_scale)

        self.screen = pygame.display.set_mode(self.display_size, display_flags)
        self.game_surface = pygame.Surface(self.logical_size)
        
        # ИЗМЕНЕНИЕ: Добавлены переменные для преобразования координат мыши
        self.render_scale = 1.0
        self.render_offset = (0, 0)

        pygame.display.set_caption("Katharsis")
        
        self.clock = pygame.time.Clock()
        
        self.logo_image = load_image("logo.png") 
        self.background_effect = RainEffect(self.game_surface)

        try:
            pygame.mixer.music.load(get_resource_path("Music", "menu.mp3"))
            pygame.mixer.music.set_volume(self.settings_manager.get_music_volume())
            pygame.mixer.music.play(-1) 
        except Exception as e:
            print(f"Не удалось загрузить музыку меню: {e}")

        self.screens = {
            "main_menu": MainMenuScreen(self.game_surface, self.settings_manager, self.background_effect, self.logo_image),
            "options": OptionsScreen(self.game_surface, self.settings_manager, self.background_effect),
            "authors": AuthorsScreen(self.game_surface, self.settings_manager, self.background_effect),
        }
        self.current_screen_name = "main_menu"
        self.current_screen = self.screens[self.current_screen_name]

    def _render_surface(self):
        self.screen.fill((0, 0, 0))
        
        # ИЗМЕНЕНИЕ: Сохраняем масштаб и смещение для расчетов мыши
        self.render_scale = min(self.display_size[0] / self.logical_size[0], self.display_size[1] / self.logical_size[1])
        scaled_width = int(self.logical_size[0] * self.render_scale)
        scaled_height = int(self.logical_size[1] * self.render_scale)
        
        scaled_surface = pygame.transform.scale(self.game_surface, (scaled_width, scaled_height))
        
        blit_x = (self.display_size[0] - scaled_width) // 2
        blit_y = (self.display_size[1] - scaled_height) // 2
        self.render_offset = (blit_x, blit_y)
        
        self.screen.blit(scaled_surface, self.render_offset)
        pygame.display.flip()

    # ИЗМЕНЕНИЕ: Новая функция для получения логических координат мыши
    def get_logical_mouse_pos(self, physical_pos=None):
        if physical_pos is None:
            physical_pos = pygame.mouse.get_pos()
        
        if self.render_scale == 0: return (0, 0)
        
        logical_x = (physical_pos[0] - self.render_offset[0]) / self.render_scale
        logical_y = (physical_pos[1] - self.render_offset[1]) / self.render_scale
        
        return int(logical_x), int(logical_y)

    def run_game(self):
        pygame.mixer.music.stop()
        
        game_instance = Game(self.game_surface, self.settings_manager.get_particles_enabled())
        game_instance.set_music_volume(self.settings_manager.get_music_volume())
        game_instance.set_sfx_volume(self.settings_manager.get_sfx_volume())
        
        pause_menu = PauseMenu(self.game_surface, self.settings_manager, None)
        
        running = True
        last_time = pygame.time.get_ticks()

        while running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - last_time) / 1000.0
            last_time = current_time
            
            dt = min(dt, 0.1)

            # ИЗМЕНЕНИЕ: Передаем исправленные координаты мыши в обработчики
            logical_mouse_pos_hover = self.get_logical_mouse_pos()
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit()

                logical_mouse_pos_click = self.get_logical_mouse_pos(event.pos) if hasattr(event, 'pos') else None

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not game_instance.game_over:
                        game_instance.paused = True
                        pause_menu.game_snapshot = self.game_surface.copy()
                        game_instance.channel_bg_music.pause()
                        
                        action = self.run_pause_menu(pause_menu)
                        if action == "main_menu":
                            game_instance.channel_bg_music.stop()
                            pygame.mixer.music.play(-1)
                            running = False 
                        elif action == "continue":
                            game_instance.paused = False
                            game_instance.channel_bg_music.unpause()
                
                if not game_instance.paused:
                    game_instance.handle_event(event)

            if not game_instance.paused:
                game_instance.handle_input(self.settings_manager.get_controls())
                game_instance.update(dt)

            game_instance.render()
            self._render_surface()
            self.clock.tick(self.settings_manager.get_max_fps())

    def run_pause_menu(self, pause_menu):
        pause_running = True
        while pause_running:
            logical_mouse_pos_hover = self.get_logical_mouse_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                
                logical_mouse_pos_click = self.get_logical_mouse_pos(event.pos) if hasattr(event, 'pos') else None
                action = pause_menu.handle_input(event, logical_mouse_pos_click)
                if action in ["continue", "main_menu"]:
                    return action

            pause_menu.update(0, logical_mouse_pos_hover)
            pause_menu.draw()
            self._render_surface()
            self.clock.tick(self.settings_manager.get_max_fps())

    def run(self):
        last_time = pygame.time.get_ticks()
        while True:
            current_time = pygame.time.get_ticks()
            dt = (current_time - last_time) / 1000.0
            last_time = current_time
            dt = min(dt, 0.1)
            
            # ИЗМЕНЕНИЕ: Передаем исправленные координаты мыши в обработчики
            logical_mouse_pos_hover = self.get_logical_mouse_pos()
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit()
                
                logical_mouse_pos_click = self.get_logical_mouse_pos(event.pos) if hasattr(event, 'pos') else None
                action = self.current_screen.handle_input(event, logical_mouse_pos_click)

                if action:
                    if action == "play":
                        self.run_game()
                        self.current_screen_name = "main_menu"
                        self.current_screen = self.screens[self.current_screen_name]
                    elif action == "exit":
                        self.quit()
                    elif action == "back":
                        self.current_screen_name = "main_menu"
                        self.current_screen = self.screens[self.current_screen_name]
                    elif action in self.screens:
                        self.current_screen_name = action
                        self.current_screen = self.screens[self.current_screen_name]
            
            self.current_screen.update(dt, logical_mouse_pos_hover)
            
            self.game_surface.fill((26, 22, 51))
            self.current_screen.draw(dt)
            self._render_surface()
            
            self.clock.tick(self.settings_manager.get_max_fps())

    def quit(self):
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.run()