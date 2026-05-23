import pygame

from circleshape import CircleShape
from constants import (
    LINE_WIDTH,
    SHOT_RADIUS,
    COLOR_SHOT,
    SHOT_LIFETIME,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class Shot(CircleShape):
    def __init__(self, x, y, radius=None, color=None, is_enemy=False):
        # Gunakan safe default jika parameter tidak didefinisikan secara eksplisit
        try:
            val_radius = float(radius) if radius is not None else float(SHOT_RADIUS)
        except (TypeError, ValueError):
            val_radius = float(SHOT_RADIUS)

        super().__init__(x, y, val_radius)
        self.lifetime = SHOT_LIFETIME
        self.is_enemy = is_enemy
        
        # Penanganan warna secara defensif
        try:
            self.color = tuple(int(c) for c in color) if color is not None else COLOR_SHOT
            if len(self.color) != 3:
                raise ValueError()
        except Exception:
            self.color = COLOR_SHOT


    def draw(self, screen):
        try:
            pygame.draw.circle(screen, self.color, self.position, self.radius, LINE_WIDTH)
        except Exception as e:
            print(f"Error drawing shot: {e}")


    def update(self, dt):
        self.position += self.velocity * dt
        self.lifetime -= dt

        # Hancurkan tembakan jika masa hidupnya habis
        if self.lifetime <= 0:
            self.kill()
            return

        # Screen wrapping untuk tembakan
        margin = self.radius
        if self.position.x < -margin:
            self.position.x = SCREEN_WIDTH + margin
        elif self.position.x > SCREEN_WIDTH + margin:
            self.position.x = -margin

        if self.position.y < -margin:
            self.position.y = SCREEN_HEIGHT + margin
        elif self.position.y > SCREEN_HEIGHT + margin:
            self.position.y = -margin

