# MultipleFiles/settings_manager.py
import configparser
import os
import pygame
from utils import get_resource_path

class SettingsManager:
    def __init__(self, settings_file="settings.ini"):
        self.settings_file = get_resource_path(settings_file)
        self.config = configparser.ConfigParser()
        self.default_settings = {
            'volume': {
                'music': '0.5',
                'sfx': '0.7'
            },
            'controls': {
                'move_left': str(pygame.K_LEFT),
                'move_right': str(pygame.K_RIGHT),
                'jump': str(pygame.K_z),
                'attack': str(pygame.K_x),
                'charge': str(pygame.K_c)
            },
            'graphics': {
                'particles': 'true'
            },
            'display': {
                'aspect_ratio': '4:3',
                'max_fps': '60',
                'window_mode': 'windowed',
                'window_scale': '2'  # НОВАЯ НАСТРОЙКА
            }
        }
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            self._create_default_settings()
        
        self.config.read(self.settings_file)
        
        for section, keys in self.default_settings.items():
            if section not in self.config:
                self.config[section] = {}
            for key, default_value in keys.items():
                if key not in self.config[section]:
                    self.config[section][key] = default_value
        self.save_settings()

    def _create_default_settings(self):
        for section, keys in self.default_settings.items():
            self.config[section] = keys
        self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as configfile:
            self.config.write(configfile)

    def get_music_volume(self):
        return float(self.config['volume']['music'])

    def set_music_volume(self, volume):
        self.config['volume']['music'] = str(volume)
        self.save_settings()

    def get_sfx_volume(self):
        return float(self.config['volume']['sfx'])

    def set_sfx_volume(self, volume):
        self.config['volume']['sfx'] = str(volume)
        self.save_settings()

    def get_controls(self):
        controls = {}
        for action, key_code_str in self.config['controls'].items():
            controls[action] = int(key_code_str)
        return controls

    def set_control(self, action, key_code):
        self.config['controls'][action] = str(key_code)
        self.save_settings()

    def get_particles_enabled(self):
        return self.config.getboolean('graphics', 'particles')

    def set_particles_enabled(self, enabled):
        self.config['graphics']['particles'] = 'true' if enabled else 'false'
        self.save_settings()

    def get_aspect_ratio(self):
        return self.config['display'].get('aspect_ratio', '4:3')

    def set_aspect_ratio(self, ratio_str):
        self.config['display']['aspect_ratio'] = ratio_str
        self.save_settings()

    def get_max_fps(self):
        fps_str = self.config['display'].get('max_fps', '60')
        if fps_str.lower() == 'unlimited':
            return 0
        return int(fps_str)

    def set_max_fps(self, fps_str):
        self.config['display']['max_fps'] = str(fps_str)
        self.save_settings()
        
    def get_window_mode(self):
        return self.config['display'].get('window_mode', 'windowed')

    def set_window_mode(self, mode_str):
        self.config['display']['window_mode'] = mode_str
        self.save_settings()
        
    # НОВЫЕ МЕТОДЫ ДЛЯ МАСШТАБА ОКНА
    def get_window_scale(self):
        scale_str = self.config['display'].get('window_scale', '2')
        return int(scale_str)

    def set_window_scale(self, scale_str):
        self.config['display']['window_scale'] = str(scale_str)
        self.save_settings()