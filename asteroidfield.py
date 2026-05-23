import random
# pyrefly: ignore [missing-import]
import pygame
from asteroid import Asteroid
from constants import *


class AsteroidField(pygame.sprite.Sprite):
    edges = [
        [
            pygame.Vector2(1, 0),
            lambda y: pygame.Vector2(-ASTEROID_MAX_RADIUS, y * SCREEN_HEIGHT),
        ],
        [
            pygame.Vector2(-1, 0),
            lambda y: pygame.Vector2(
                SCREEN_WIDTH + ASTEROID_MAX_RADIUS, y * SCREEN_HEIGHT
            ),
        ],
        [
            pygame.Vector2(0, 1),
            lambda x: pygame.Vector2(x * SCREEN_WIDTH, -ASTEROID_MAX_RADIUS),
        ],
        [
            pygame.Vector2(0, -1),
            lambda x: pygame.Vector2(
                x * SCREEN_WIDTH, SCREEN_HEIGHT + ASTEROID_MAX_RADIUS
            ),
        ],
    ]

    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.spawn_timer = 0.0
        self.level = 1

    def spawn(self, radius, position, velocity, asteroid_type="normal"):
        asteroid = Asteroid(position.x, position.y, radius, asteroid_type)
        asteroid.velocity = velocity

    def update(self, dt):
        self.spawn_timer += dt
        
        # Kecepatan spawn bertambah cepat seiring bertambahnya level
        # Batasi spawn_rate minimum di 0.25 detik agar game tetap bisa dimainkan
        spawn_rate = max(0.25, ASTEROID_SPAWN_RATE_SECONDS / (1.0 + (self.level - 1) * 0.15))
        
        if self.spawn_timer > spawn_rate:
            self.spawn_timer = 0

            # spawn a new asteroid at a random edge
            edge = random.choice(self.edges)
            
            # Kecepatan asteroid meningkat seiring level
            speed_min = 40 + (self.level - 1) * 10
            speed_max = 100 + (self.level - 1) * 15
            speed = random.randint(speed_min, speed_max)
            
            velocity = edge[0] * speed
            velocity = velocity.rotate(random.randint(-30, 30))
            position = edge[1](random.uniform(0, 1))
            kind = random.randint(1, ASTEROID_KINDS)
            
            # Tentukan tipe asteroid secara acak
            # 60% Normal, 20% Crystal, 20% Magnetic
            roll = random.random()
            if roll < 0.60:
                asteroid_type = "normal"
            elif roll < 0.80:
                asteroid_type = "crystal"
            else:
                asteroid_type = "magnetic"
                
            self.spawn(ASTEROID_MIN_RADIUS * kind, position, velocity, asteroid_type)


