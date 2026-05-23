import random
import pygame
import math
from circleshape import CircleShape
from constants import (
    LINE_WIDTH,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)

class Powerup(CircleShape):
    """
    Entitas Powerup yang dijatuhkan dari asteroid yang hancur.
    Memberikan peningkatan status/senjata sementara kepada Player.
    """
    def __init__(self, x: float, y: float, kind: str):
        # Validasi input secara defensif
        try:
            val_x = float(x)
            val_y = float(y)
            val_kind = str(kind).strip().lower()
            if val_kind not in ["shield", "triple", "rapid"]:
                raise ValueError(f"Unknown powerup kind: {val_kind}")
        except (TypeError, ValueError) as e:
            # Fallback ke nilai aman jika input tidak valid
            val_x = SCREEN_WIDTH / 2
            val_y = SCREEN_HEIGHT / 2
            val_kind = "shield"
            print(f"Warning: Powerup initialization error: {e}. Falling back to default values.")

        super().__init__(val_x, val_y, 15)
        self.kind = val_kind
        self.rotation = 0.0

        # Tentukan skema warna dan inisial teks berdasarkan jenis power-up
        if self.kind == "shield":
            self.color = (0, 240, 255)      # Cyan
            self.letter = "S"
        elif self.kind == "triple":
            self.color = (255, 220, 0)      # Kuning
            self.letter = "T"
        else: # "rapid"
            self.color = (50, 255, 100)     # Hijau
            self.letter = "R"

        # Hanyut dengan kecepatan lambat ke arah acak
        angle = random.uniform(0, 360)
        try:
            self.velocity = pygame.Vector2(0, 1).rotate(angle) * random.uniform(30.0, 60.0)
        except Exception:
            self.velocity = pygame.Vector2(30.0, 30.0)

    def draw(self, screen: pygame.Surface):
        """
        Menggambar bentuk heksagon neon berputar secara defensif dengan teks inisial di tengah.
        """
        if not isinstance(screen, pygame.Surface):
            return

        try:
            # Menggambar kerangka heksagon neon berputar
            points = []
            for i in range(6):
                pt_angle = self.rotation + i * 60
                # Hitung koordinat titik sudut secara defensif
                offset = pygame.Vector2(0, self.radius).rotate(pt_angle)
                points.append(self.position + offset)

            # Gambar glow tipis di bawahnya (double line effect)
            pygame.draw.polygon(screen, tuple(max(0, c - 80) for c in self.color), points, LINE_WIDTH + 2)
            pygame.draw.polygon(screen, self.color, points, LINE_WIDTH)

            # Gambar teks inisial di tengah
            font = pygame.font.Font(None, 24)
            text_surf = font.render(self.letter, True, self.color)
            text_rect = text_surf.get_rect()
            text_rect.center = (int(self.position.x), int(self.position.y))
            screen.blit(text_surf, text_rect)
        except Exception as e:
            # Mencegah crash jika kegagalan font atau penggambaran terjadi
            print(f"Error drawing powerup: {e}")

    def update(self, dt: float):
        """
        Perbarui posisi dan rotasi powerup secara defensif.
        """
        try:
            val_dt = float(dt)
        except (TypeError, ValueError):
            val_dt = 0.0

        try:
            self.position += self.velocity * val_dt
            self.rotation += 90.0 * val_dt  # Putar 90 derajat per detik
        except Exception as e:
            print(f"Error updating powerup position: {e}")

        # Screen wrapping agar powerup tidak keluar layar
        margin = self.radius
        if self.position.x < -margin:
            self.position.x = SCREEN_WIDTH + margin
        elif self.position.x > SCREEN_WIDTH + margin:
            self.position.x = -margin

        if self.position.y < -margin:
            self.position.y = SCREEN_HEIGHT + margin
        elif self.position.y > SCREEN_HEIGHT + margin:
            self.position.y = -margin
