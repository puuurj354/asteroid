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
    def __init__(self, x, y, radius=None, color=None, is_enemy=False, homing_groups=None):
        # Gunakan safe default jika parameter tidak didefinisikan secara eksplisit
        try:
            val_radius = float(radius) if radius is not None else float(SHOT_RADIUS)
        except (TypeError, ValueError):
            val_radius = float(SHOT_RADIUS)

        super().__init__(x, y, val_radius)
        self.lifetime      = SHOT_LIFETIME
        self.is_enemy      = is_enemy
        # homing_groups: tuple of pygame.sprite.Group — diset saat homing powerup aktif
        self.homing_groups = homing_groups if not is_enemy else None
        
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
        # Homing: belokkan peluru perlahan ke target terdekat
        if self.homing_groups is not None:
            self._steer_toward_nearest(dt)

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

    def _steer_toward_nearest(self, dt: float):
        """
        Belokkan velocity peluru secara halus menuju target terdekat
        dari semua group yang diberikan. Max turn rate: 200 deg/detik.
        """
        nearest  = None
        min_dist = float("inf")
        try:
            for group in self.homing_groups:
                for target in group:
                    if not target.alive():
                        continue
                    d = self.position.distance_to(target.position)
                    if d < min_dist:
                        min_dist = d
                        nearest  = target
        except Exception:
            return

        if nearest is None:
            return

        try:
            to_target = nearest.position - self.position
            if to_target.length_squared() == 0:
                return
            speed      = self.velocity.length()
            target_dir = to_target.normalize()
            current_dir = self.velocity.normalize() if speed > 0 else target_dir
            # Lerp ke arah target — koefisien = turn rate
            new_dir = current_dir.lerp(target_dir, min(1.0, 3.8 * dt))
            if new_dir.length() > 0:
                self.velocity = new_dir.normalize() * speed
        except Exception:
            pass

