import random
# pyrefly: ignore [missing-import]
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Star:
    """
    Representasi sebuah bintang tunggal di latar belakang.
    """
    def __init__(self, x: float, y: float, speed: float, radius: float, brightness: int):
        self.x = float(x)
        self.y = float(y)
        self.speed = float(speed)
        self.radius = float(radius)
        # Warna abu-abu/putih tergantung tingkat kecerahan
        brightness_val = max(50, min(255, int(brightness)))
        self.color = (brightness_val, brightness_val, min(255, brightness_val + 20))

    def update(self, dt: float, direction: pygame.Vector2):
        """
        Perbarui posisi bintang berdasarkan arah hanyut (drift direction).
        """
        try:
            self.x += direction.x * self.speed * dt
            self.y += direction.y * self.speed * dt

            # Screen wrapping untuk bintang
            if self.x < 0:
                self.x = SCREEN_WIDTH
                self.y = random.uniform(0, SCREEN_HEIGHT)
            elif self.x > SCREEN_WIDTH:
                self.x = 0
                self.y = random.uniform(0, SCREEN_HEIGHT)

            if self.y < 0:
                self.y = SCREEN_HEIGHT
                self.x = random.uniform(0, SCREEN_WIDTH)
            elif self.y > SCREEN_HEIGHT:
                self.y = 0
                self.x = random.uniform(0, SCREEN_WIDTH)
        except Exception as e:
            # Defensive handler
            print(f"Error updating star: {e}")

    def draw(self, screen: pygame.Surface):
        """
        Gambarkan bintang ke layar.
        """
        try:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        except Exception as e:
            print(f"Error drawing star: {e}")


class Starfield:
    """
    Mengelola banyak lapisan bintang untuk menciptakan efek parallax.
    """
    def __init__(self, num_stars: int = 120):
        self.stars: list[Star] = []
        self.drift_direction = pygame.Vector2(-0.5, -0.5).normalize()  # Drift diagonal lambat
        
        # Defensive check
        try:
            num_stars = int(num_stars)
        except (TypeError, ValueError):
            num_stars = 120

        # Memisahkan bintang ke dalam 3 lapisan kedalaman (parallax)
        for _ in range(num_stars):
            x = random.uniform(0, SCREEN_WIDTH)
            y = random.uniform(0, SCREEN_HEIGHT)
            layer = random.choice([1, 2, 3])

            if layer == 1:
                # Lapisan Jauh (sangat lambat, kecil, redup)
                speed = random.uniform(2.0, 6.0)
                radius = 1.0
                brightness = random.randint(80, 130)
            elif layer == 2:
                # Lapisan Menengah (sedang)
                speed = random.uniform(8.0, 15.0)
                radius = 1.5
                brightness = random.randint(140, 190)
            else:
                # Lapisan Dekat (cepat, besar, cerang)
                speed = random.uniform(18.0, 30.0)
                radius = 2.0
                brightness = random.randint(200, 255)

            self.stars.append(Star(x, y, speed, radius, brightness))

    def update(self, dt: float):
        """
        Perbarui semua bintang dalam starfield.
        """
        try:
            dt = float(dt)
        except (TypeError, ValueError):
            dt = 0.0

        for star in self.stars:
            star.update(dt, self.drift_direction)

    def draw(self, screen: pygame.Surface):
        """
        Gambarkan seluruh starfield ke layar.
        """
        if not isinstance(screen, pygame.Surface):
            return
            
        for star in self.stars:
            star.draw(screen)
