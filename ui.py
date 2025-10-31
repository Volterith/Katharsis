import pygame
from utils import load_font

class UIManager:
    def __init__(self):
        self.floating_texts = []
        self.font = load_font("munro.otf", 24)
        self.large_font = load_font("munro.otf", 48)
        self.coin_icon = self._load_coin_icon()
        self.heart_icon = self._load_heart_icon()
        self.coins_collected = 0
        self.max_health = 5
        self.player = None
        
        self.coin_counter_visible = False
        self.coin_counter_alpha = 0
        self.coin_counter_timer = 0
        self.coin_counter_show_time = 3.0
        
        self.game_over = False
        self.game_over_alpha = 0
        self.game_over_target_alpha = 220
        self.game_over_fade_speed = 100

        self.showing_intro = True
        self.intro_alpha = 0
        self.intro_fade_speed = 0.8
        self.intro_texts = [
            "Мрачный лес",
            "По приказу свыше вы отправляетесь в приключение,",
            "в котором вам нужно побеждать существ,",
            "души которых подвержены неизвестной болезни."
        ]
        self.show_prompt = False
        self.prompt_alpha = 0
        self.prompt_timer = 0
        self.prompt_delay = 3.0

        self.showing_demo_end = False
        self.demo_end_alpha = 0
        self.demo_end_fade_speed = 150
        self.demo_end_texts = ["Спасибо за игру!", "Демо-версия окончена."]

    @property
    def current_health(self):
        return self.player.current_health if self.player else 0

    def _load_coin_icon(self):
        try:
            return pygame.image.load("Sprites/coin.png").convert_alpha()
        except:
            icon = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(icon, (255, 223, 0), (12, 12), 10)
            return icon

    def _load_heart_icon(self):
        try:
            return pygame.image.load("Sprites/heart.png").convert_alpha()
        except:
            icon = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.polygon(icon, (255, 0, 0), [(12, 0), (23, 8), (19, 23), (5, 23), (0, 8)])
            return icon

    def start_intro(self):
        self.showing_intro = True
        self.intro_alpha = 0
        self.show_prompt = False
        self.prompt_alpha = 0
        self.prompt_timer = 0
        self.showing_demo_end = False

    def skip_intro(self):
        self.showing_intro = False

    def show_demo_end_screen(self):
        self.showing_demo_end = True
        self.demo_end_alpha = 0
        self.showing_intro = False
        self.game_over = False

    def update_intro(self, dt):
        if not self.showing_intro: return
        if self.intro_alpha < 200:
            self.intro_alpha = min(200, self.intro_alpha + self.intro_fade_speed * dt * 100)
        self.prompt_timer += dt
        if self.prompt_timer >= self.prompt_delay:
            self.show_prompt = True
            if self.prompt_alpha < 255:
                self.prompt_alpha = min(255, self.prompt_alpha + self.intro_fade_speed * dt * 150)

    def draw_intro(self, surface):
        if not self.showing_intro: return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.intro_alpha))
        surface.blit(overlay, (0, 0))
        
        title = self.large_font.render(self.intro_texts[0], True, (255, 255, 255))
        title.set_alpha(self.intro_alpha)
        title_rect = title.get_rect(center=(surface.get_width()//2, surface.get_height()//2 - 50))
        surface.blit(title, title_rect)
        
        for i, line in enumerate(self.intro_texts[1:]):
            text = self.font.render(line, True, (255, 255, 255))
            text.set_alpha(self.intro_alpha)
            text_rect = text.get_rect(center=(surface.get_width()//2, surface.get_height()//2 + 20 + i*30))
            surface.blit(text, text_rect)
        
        if self.show_prompt:
            prompt = self.font.render("Нажмите ENTER чтобы начать", True, (200, 200, 200))
            prompt.set_alpha(self.prompt_alpha)
            prompt_rect = prompt.get_rect(center=(surface.get_width()//2, surface.get_height() - 50))
            surface.blit(prompt, prompt_rect)

    def draw_demo_end_screen(self, surface):
        if not self.showing_demo_end: return
        overlay = pygame.Surface(surface.get_size())
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        if self.demo_end_alpha > 0:
            for i, line in enumerate(self.demo_end_texts):
                text = self.large_font.render(line, True, (255, 255, 255))
                text.set_alpha(int(self.demo_end_alpha))
                text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 30 + i * 60))
                surface.blit(text, text_rect)

    def show_coin_counter(self):
        self.coin_counter_visible = True
        self.coin_counter_timer = self.coin_counter_show_time
        self.coin_counter_alpha = 255

    def create_floating_text(self, text, position, color=(255, 255, 255)):
        self.floating_texts.append(FloatingText(text, self.font, position, color))

    def update(self, dt, game_paused=False):
        for ft in self.floating_texts[:]:
            ft.update(dt)
            if ft.alpha <= 0: self.floating_texts.remove(ft)
        
        if game_paused: self.coin_counter_alpha = 255
        else:
            if self.coin_counter_visible:
                self.coin_counter_timer -= dt
                if self.coin_counter_timer <= 0: self.coin_counter_visible = False
                self.coin_counter_alpha = int(255 * min(1, self.coin_counter_timer * 2))
        
        if self.game_over and self.game_over_alpha < self.game_over_target_alpha:
            self.game_over_alpha = min(self.game_over_target_alpha, self.game_over_alpha + self.game_over_fade_speed * dt)
        
        if self.showing_demo_end and self.demo_end_alpha < 255:
            self.demo_end_alpha = min(255, self.demo_end_alpha + self.demo_end_fade_speed * dt)

    def draw(self, surface):
        if self.showing_intro or self.showing_demo_end: return

        if self.coin_counter_alpha > 0:
            icon = self.coin_icon.copy()
            icon.set_alpha(self.coin_counter_alpha)
            surface.blit(icon, (10, 10))
            text_surf = self.font.render(f"x {self.coins_collected}", True, (255, 255, 255))
            text_surf.set_alpha(self.coin_counter_alpha)
            surface.blit(text_surf, (44, 16))

        for i in range(self.max_health):
            heart_pos = (surface.get_width() - 30 * (i + 1), 10)
            if i < self.current_health:
                surface.blit(self.heart_icon, heart_pos)
            else:
                empty_heart = self.heart_icon.copy()
                empty_heart.fill((50, 50, 50, 150), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(empty_heart, heart_pos)

        if self.game_over:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self.game_over_alpha))
            surface.blit(overlay, (0, 0))
            if self.game_over_alpha >= self.game_over_target_alpha:
                text = self.large_font.render("ПОТРАЧЕНО", True, (255, 50, 50))
                text_rect = text.get_rect(center=(surface.get_width()//2, surface.get_height()//2 - 30))
                surface.blit(text, text_rect)
                hint = self.font.render("Нажмите ENTER чтобы начать сначала", True, (255, 255, 255))
                hint_rect = hint.get_rect(center=(surface.get_width()//2, surface.get_height()//2 + 30))
                surface.blit(hint, hint_rect)

        for ft in self.floating_texts:
            ft.draw(surface)

class FloatingText:
    def __init__(self, text, font, pos, color=(255, 255, 255)):
        self.font = font
        self.pos = pygame.Vector2(pos)
        self.alpha = 255
        self.lifetime = 1.0
        self.elapsed = 0.0
        self.image = self.font.render(text, True, color).convert_alpha()
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.lifetime:
            self.alpha = 0
        else:
            self.pos.y -= 50 * dt
            self.alpha = int(255 * (1 - self.elapsed / self.lifetime))
            self.image.set_alpha(self.alpha) 
            self.rect.center = self.pos

    def draw(self, surface):
        if self.alpha > 0:
            surface.blit(self.image, self.rect)