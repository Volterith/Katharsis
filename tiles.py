# tiles.py

import pygame
import xml.etree.ElementTree as ET
import os
import random
from enemies import MeleeGhost, RangedGhost, EtherJumperBoss

class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, properties=None):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.properties = properties or {}

class CollectableTile(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))

class PlatformTile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, properties=None):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.properties = properties or {}

class FallingTile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, fall_on_stand, fall_on_pass_under, respawn_time):
        super().__init__()
        self.original_image = image
        self.image = image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.fall_on_stand = fall_on_stand
        self.fall_on_pass_under = fall_on_pass_under
        self.respawn_time = respawn_time
        self.falling = False
        self.shaking = False
        self.shake_timer = 0.0
        self.fall_timer = 0.0
        self.respawn_timer = 0.0
        self.original_pos = (x, y)
        self.visible = True
        self.shake_offset = 0

    def start_shaking(self):
        if not self.falling and not self.shaking:
            self.shaking = True
            self.shake_timer = 0.5

    def update(self, dt):
        if not self.visible:
            self.respawn_timer += dt
            if self.respawn_timer >= self.respawn_time:
                self.visible = True
                self.falling = False
                self.shaking = False
                self.rect.topleft = self.original_pos
            return

        if self.shaking:
            self.shake_timer -= dt
            self.shake_offset = (self.shake_offset + 1) % 4 - 2
            self.rect.x = self.original_pos[0] + self.shake_offset
            if self.shake_timer <= 0:
                self.shaking = False
                self.falling = True
                self.rect.x = self.original_pos[0]
        
        if self.falling:
            self.rect.y += 300 * dt
            if self.rect.top > self.original_pos[1] + 600:
                self.visible = False

class BreakableTile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, properties=None):
        super().__init__()
        self.original_image = image
        self.image = image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.properties = properties or {}
        self.health = self.properties.get('health', 1)
        self.broken = False
        self.particles = []
        self.collidable = self.properties.get('collidable', True)
        
    def take_damage(self, amount, particles_enabled=True):
        if not self.broken and self.collidable:
            self.health -= amount
            if self.health <= 0:
                self.break_tile(particles_enabled)
                return True
        return False
    
    def break_tile(self, particles_enabled=True):
        if self.broken: return
        self.broken = True
        self.collidable = False
        if particles_enabled:
            self.create_particles()
        
    def create_particles(self):
        width, height = self.original_image.get_size()
        particle_size = 8
        for i in range(0, width, particle_size):
            for j in range(0, height, particle_size):
                particle_img = self.original_image.subsurface(pygame.Rect(i, j, particle_size, particle_size))
                self.particles.append({
                    'image': particle_img, 'pos': [self.rect.x + i, self.rect.y + j],
                    'velocity': [random.uniform(-2, 2), random.uniform(-4, 0)],
                    'gravity': 0.2, 'lifetime': random.uniform(0.8, 1.5), 'timer': 0
                })
    
    def update(self, dt):
        if self.broken:
            if not self.particles: self.kill()
            for p in self.particles[:]:
                p['timer'] += dt
                p['pos'][0] += p['velocity'][0] 
                p['pos'][1] += p['velocity'][1]
                p['velocity'][1] += p['gravity']
                if p['timer'] >= p['lifetime']: self.particles.remove(p)
    
    def draw(self, surface, camera):
        if not self.broken:
            surface.blit(self.image, camera.apply(self.rect))
        else:
            for p in self.particles:
                alpha = max(0, 255 * (1 - p['timer'] / p['lifetime']))
                img_copy = p['image'].copy(); img_copy.set_alpha(alpha)
                surface.blit(img_copy, camera.apply(pygame.Rect(p['pos'], p['image'].get_size())))

class HealingTile(Tile):
    def __init__(self, image, x, y, properties=None):
        super().__init__(image, x, y, properties)
        self.active = True
        self.respawn_time = properties.get('respawn_time', 30.0)
        self.respawn_timer = 0.0
        
    def update(self, dt):
        if not self.active:
            self.respawn_timer += dt
            if self.respawn_timer >= self.respawn_time:
                self.active = True
                self.respawn_timer = 0.0
                
    def use(self):
        if self.active:
            self.active = False
            return True
        return False
        
    def draw(self, surface, camera):
        if self.active:
            surface.blit(self.image, camera.apply(self.rect))
        else:
            temp_image = self.image.copy()
            temp_image.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(temp_image, camera.apply(self.rect))

class MapLoader:
    def __init__(self):
        self.obstacles = pygame.sprite.Group()
        self.collectables = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.falling_tiles = pygame.sprite.Group()
        self.breakable_tiles = pygame.sprite.Group()
        self.healing_tiles = pygame.sprite.Group()
        self.enemies_data = []
        self.player_spawn_pos = (100, 100)
        self.layer1 = None
        self.layer2 = None
        self.map_width = 0
        self.map_height = 0
        self.tile_properties = {}
        self.tileset_images = {}
        self.static_surface = None

    def parse_properties(self, node):
        properties = {}
        for prop in node.findall('properties/property'):
            name, value, prop_type = prop.get('name'), prop.get('value'), prop.get('type')
            if prop_type == 'bool': properties[name] = value == 'true'
            elif prop_type == 'int': properties[name] = int(value)
            elif prop_type == 'float': properties[name] = float(value)
            else: properties[name] = value
        return properties

    def load_map(self, map_path):
        tree = ET.parse(map_path)
        root = tree.getroot()
        self.map_width = int(root.get('width')) * int(root.get('tilewidth'))
        self.map_height = int(root.get('height')) * int(root.get('tileheight'))
        tilewidth, tileheight = int(root.get('tilewidth')), int(root.get('tileheight'))

        for ts in root.findall('tileset'):
            firstgid = int(ts.get('firstgid'))
            tileset_source = ts.get('source')
            if tileset_source:
                tileset_path = os.path.join(os.path.dirname(map_path), tileset_source)
                tileset_tree = ET.parse(tileset_path)
                tileset_root = tileset_tree.getroot()
                image_node = tileset_root.find('image')
                image_path = os.path.join(os.path.dirname(tileset_path), image_node.get('source'))
                tileset_image = pygame.image.load(image_path).convert_alpha()
                for tile_node in tileset_root.findall('tile'):
                    self.tile_properties[firstgid + int(tile_node.get('id'))] = self.parse_properties(tile_node)
            else:
                image_node = ts.find('image')
                image_path = os.path.join(os.path.dirname(map_path), image_node.get('source'))
                tileset_image = pygame.image.load(image_path).convert_alpha()

            img_w, img_h = tileset_image.get_size()
            for tile_id in range((img_w // tilewidth) * (img_h // tileheight)):
                gid = firstgid + tile_id
                x = (tile_id % (img_w // tilewidth)) * tilewidth
                y = (tile_id // (img_w // tilewidth)) * tileheight
                self.tileset_images[gid] = tileset_image.subsurface(pygame.Rect(x, y, tilewidth, tileheight))
        
        for group in [self.obstacles, self.collectables, self.platforms, self.falling_tiles, self.breakable_tiles, self.healing_tiles]: group.empty()
        self.enemies_data = []

        try:
            self.layer1 = pygame.image.load("Rooms/layer1.png").convert_alpha()
            self.layer2 = pygame.image.load("Rooms/layer2.png").convert_alpha()
        except pygame.error:
            self.layer1 = pygame.Surface((self.map_width, 480), pygame.SRCALPHA)
            self.layer2 = pygame.Surface((self.map_width, 480), pygame.SRCALPHA)

        static_tiles = []
        for layer in root.findall('layer'):
            data_node = layer.find('data')
            if data_node is not None and data_node.get('encoding') == 'csv' and data_node.text:
                for y, row in enumerate(data_node.text.strip().split('\n')):
                    stripped_row = row.strip()
                    if not stripped_row: continue
                    for x, gid_str in enumerate(stripped_row.split(',')):
                        # *** ИСПРАВЛЕНИЕ ЗДЕСЬ ***
                        # Проверяем, что строка не пустая, прежде чем преобразовывать в int
                        if gid_str:
                            gid = int(gid_str)
                            if gid != 0:
                                self._process_tile(x, y, gid, tilewidth, tileheight, static_tiles)
        self._pre_render_static_layers(static_tiles)

    def _process_tile(self, x, y, gid, tw, th, static_tiles):
        tile_image = self.tileset_images.get(gid)
        if not tile_image: return
        props = self.tile_properties.get(gid, {})
        wx, wy = x * tw, y * th

        if props.get('player_spawn'): self.player_spawn_pos = (wx, wy)
        elif props.get('enemy'): self.enemies_data.append({'type': props.get('type'), 'pos': (wx, wy), 'properties': props})
        elif props.get('collectable'): self.collectables.add(CollectableTile(tile_image, wx, wy))
        elif props.get('fall'): self.falling_tiles.add(FallingTile(tile_image, wx, wy, props.get('fall_on_stand', True), props.get('fall_on_pass_under', False), props.get('respawn_time', 5.0)))
        elif props.get('breakable'):
            new_tile = BreakableTile(tile_image, wx, wy, props)
            self.breakable_tiles.add(new_tile)
            if new_tile.collidable: self.obstacles.add(new_tile)
        elif props.get('healing'): self.healing_tiles.add(HealingTile(tile_image, wx, wy, props))
        else:
            new_tile = Tile(tile_image, wx, wy, props)
            if props.get('collidable'): self.obstacles.add(new_tile)
            if props.get('platform'): self.platforms.add(PlatformTile(tile_image, wx, wy, props))
            static_tiles.append(new_tile)

    def _pre_render_static_layers(self, static_tiles):
        self.static_surface = pygame.Surface((self.map_width, self.map_height), pygame.SRCALPHA)
        for tile in static_tiles:
            self.static_surface.blit(tile.image, tile.rect)

    def draw_static_tiles(self, surface, camera):
        surface.blit(self.static_surface, camera.apply(self.static_surface.get_rect()))

    def draw_dynamic_tiles(self, surface, camera):
        for tile in self.falling_tiles:
            if tile.visible: surface.blit(tile.image, camera.apply(tile.rect))
        for tile in self.breakable_tiles: tile.draw(surface, camera)
        for coin in self.collectables: surface.blit(coin.image, camera.apply(coin.rect))
        for healing_tile in self.healing_tiles: healing_tile.draw(surface, camera)

    def draw_parallax_background(self, surface, camera_x, camera_y):
        screen_width, screen_height = surface.get_size()
        l1_w, l1_h = self.layer1.get_size()
        l2_w, l2_h = self.layer2.get_size()
        start_offset_x = 128
        start_offset_y = 550
        parallax_x_2 = (start_offset_x - camera_x * 0.8) % l2_w - l2_w
        parallax_y_2 = start_offset_y - camera_y * 0.8
        parallax_x_1 = (start_offset_x - camera_x * 0.8) % l1_w - l1_w
        parallax_y_1 = start_offset_y - camera_y * 0.8
        
        x = parallax_x_2
        while x < screen_width:
            surface.blit(self.layer2, (x, parallax_y_2))
            x += l2_w
        
        x = parallax_x_1
        while x < screen_width:
            surface.blit(self.layer1, (x, parallax_y_1))
            x += l1_w