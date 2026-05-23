import random
# pyrefly: ignore [missing-import]
import pygame
import math

from circleshape import CircleShape
from constants import (
    ASTEROID_MIN_RADIUS,
    LINE_WIDTH,
    COLOR_ASTEROID,
    COLOR_CRYSTAL,
    COLOR_MAGNETIC,
    MAGNETIC_INFLUENCE_RADIUS,
    MAGNETIC_PULL_FORCE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
from logger import log_event
from particles import spawn_explosion_particles


class Asteroid(CircleShape):
    def __init__(self, x, y, radius, asteroid_type="normal"):
        super().__init__(x, y, radius)
        self.asteroid_type = asteroid_type

        # Konfigurasi warna berdasarkan tipe
        if self.asteroid_type == "crystal":
            self.color = COLOR_CRYSTAL
            # Buat titik-titik sudut polygon acak statis untuk visual kristal tak beraturan
            self.vertices = []
            num_vertices = random.randint(6, 9)
            for i in range(num_vertices):
                angle = (i * 2 * math.pi) / num_vertices
                # Variasi radius untuk siluet yang tidak rata
                r = self.radius * random.uniform(0.75, 1.15)
                offset = pygame.Vector2(0, r).rotate(math.degrees(angle))
                self.vertices.append(offset)
        elif self.asteroid_type == "magnetic":
            self.color = COLOR_MAGNETIC
        else:
            self.color = COLOR_ASTEROID

    def draw(self, screen):
        try:
            if self.asteroid_type == "crystal" and hasattr(self, "vertices"):
                # Gambar bentuk kristal polygon
                points = [self.position + offset for offset in self.vertices]
                # Gambar outline neon tebal tipis agar menyala
                glow_color = tuple(max(0, c - 70) for c in self.color)
                pygame.draw.polygon(screen, glow_color, points, LINE_WIDTH + 2)
                pygame.draw.polygon(screen, self.color, points, LINE_WIDTH)
            elif self.asteroid_type == "magnetic":
                # Gambar lingkaran utama asteroid magnetik
                pygame.draw.circle(screen, self.color, self.position, self.radius, LINE_WIDTH)
                
                # Gambar aura magnetik berdenyut
                ticks = pygame.time.get_ticks()
                pulse_radius = self.radius + 12 + math.sin(ticks / 100.0) * 6.0
                
                # Gambar riak aura berupa garis-garis tipis mengelilinginya (ring putus-putus)
                for i in range(12):
                    angle = i * 30 + (ticks / 15.0) % 360
                    dash_start = self.position + pygame.Vector2(0, pulse_radius).rotate(angle)
                    dash_end = self.position + pygame.Vector2(0, pulse_radius + 4.0).rotate(angle)
                    pygame.draw.line(screen, self.color, dash_start, dash_end, 1)
            else:
                # Gambar asteroid normal
                pygame.draw.circle(screen, self.color, self.position, self.radius, LINE_WIDTH)
        except Exception as e:
            # Fallback jika terjadi error penggambaran
            pygame.draw.circle(screen, self.color, self.position, self.radius, LINE_WIDTH)
            print(f"Error drawing asteroid: {e}")

    def update(self, dt, player=None):
        # Update posisi
        self.position += self.velocity * dt

        # Logika medan tarik magnet jika bertipe magnetic
        if self.asteroid_type == "magnetic" and player is not None:
            try:
                distance = self.position.distance_to(player.position)
                if distance < MAGNETIC_INFLUENCE_RADIUS and distance > 5.0:
                    # Tarik kapal pemain ke arah asteroid
                    direction = (self.position - player.position).normalize()
                    # Gaya tarik semakin kuat jika semakin dekat (berbanding terbalik)
                    factor = 1.0 - (distance / MAGNETIC_INFLUENCE_RADIUS)
                    pull_vector = direction * (MAGNETIC_PULL_FORCE * factor * dt)
                    
                    # Tambahkan kecepatan tarikan ke player.velocity secara defensif
                    player.velocity += pull_vector
            except Exception as e:
                print(f"Error applying magnetic pull: {e}")

        # Screen wrapping agar asteroid membungkus layar
        margin = self.radius
        if self.position.x < -margin:
            self.position.x = SCREEN_WIDTH + margin
        elif self.position.x > SCREEN_WIDTH + margin:
            self.position.x = -margin

        if self.position.y < -margin:
            self.position.y = SCREEN_HEIGHT + margin
        elif self.position.y > SCREEN_HEIGHT + margin:
            self.position.y = -margin

    def split(self):
        # Ledakan partikel saat hancur sesuai warna tipe asteroid
        spawn_explosion_particles(self.position.x, self.position.y, 18, self.color)

        self.kill()

        if self.radius <= ASTEROID_MIN_RADIUS:
            return

        log_event("asteroid_split", asteroid_type=self.asteroid_type)

        new_radius = self.radius - ASTEROID_MIN_RADIUS

        if self.asteroid_type == "crystal":
            # Asteroid kristal pecah menjadi 3 serpihan kecil sekaligus
            angles = [-40.0, 0.0, 40.0]
            for angle in angles:
                try:
                    new_vel = self.velocity.rotate(angle) * 1.5  # Kecepatan lebih tinggi (1.5x)
                    ast = Asteroid(self.position.x, self.position.y, new_radius, self.asteroid_type)
                    ast.velocity = new_vel
                except Exception as e:
                    print(f"Error splitting crystal asteroid: {e}")
        else:
            # Asteroid biasa & magnetik pecah menjadi 2 bagian seperti biasa
            try:
                angle = random.uniform(20.0, 50.0)
                new_velocity_1 = self.velocity.rotate(angle) * 1.2
                new_velocity_2 = self.velocity.rotate(-angle) * 1.2

                asteroid_1 = Asteroid(self.position.x, self.position.y, new_radius, self.asteroid_type)
                asteroid_1.velocity = new_velocity_1

                asteroid_2 = Asteroid(self.position.x, self.position.y, new_radius, self.asteroid_type)
                asteroid_2.velocity = new_velocity_2
            except Exception as e:
                print(f"Error splitting normal/magnetic asteroid: {e}")


