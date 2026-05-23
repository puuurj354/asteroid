import random
import pygame


class Particle(pygame.sprite.Sprite):
    """
    Representasi sebuah partikel efek visual sederhana yang menyusut dan memudar seiring waktu.
    """

    def __init__(self, x: float, y: float, velocity: pygame.Vector2, color: tuple[int, int, int], duration: float, max_radius: float = 4.0):
        if not hasattr(self, "containers"):
            super().__init__()
        else:
            super().__init__(self.containers)

        # Defensive input check
        try:
            self.position = pygame.Vector2(float(x), float(y))
            self.velocity = pygame.Vector2(velocity)
            self.color = tuple(int(c) for c in color)
            if len(self.color) != 3:
                raise ValueError("Color must be a tuple of 3 integers.")
        except (TypeError, ValueError) as e:
            # Fallback to safe defaults if inputs are invalid
            self.position = pygame.Vector2(0, 0)
            self.velocity = pygame.Vector2(0, 0)
            self.color = (255, 255, 255)
            # Log error internally or print to stdout defensively
            print(f"Warning: Invalid Particle initialization parameters: {e}. Fallback to defaults used.")

        self.duration = max(0.01, float(duration))
        self.max_radius = max(1.0, float(max_radius))
        self.age = 0.0

    def update(self, dt: float):
        """
        Perbarui umur dan posisi partikel.
        """
        try:
            dt = float(dt)
        except (TypeError, ValueError):
            dt = 0.0

        self.age += dt
        self.position += self.velocity * dt

        # Jika umur partikel melebihi durasinya, hapus dari semua sprite group
        if self.age >= self.duration:
            self.kill()

    def draw(self, screen: pygame.Surface):
        """
        Gambarkan partikel di layar dengan ukuran yang menyusut seiring bertambahnya umur.
        """
        if not isinstance(screen, pygame.Surface):
            return

        try:
            # Hitung rasio umur partikel (0.0 di awal, mendekati 1.0 di akhir)
            life_ratio = min(1.0, self.age / self.duration)
            
            # Radius menyusut secara linear
            current_radius = self.max_radius * (1.0 - life_ratio)
            if current_radius < 0.5:
                return

            # Mengubah warna seiring bertambahnya umur (misal: orange -> merah)
            # Menghitung interpolasi warna secara defensif
            r = int(self.color[0] * (1.0 - life_ratio * 0.5))
            g = int(self.color[1] * (1.0 - life_ratio))
            b = int(self.color[2] * (1.0 - life_ratio))
            
            # Pastikan nilai warna dalam rentang 0-255
            color = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b))
            )

            pygame.draw.circle(screen, color, self.position, current_radius)
        except Exception as e:
            # Defensive catch to prevent crashes during drawing
            print(f"Error drawing particle: {e}")


def spawn_explosion_particles(x: float, y: float, count: int, color: tuple[int, int, int], speed_range: tuple[float, float] = (50.0, 150.0)):
    """
    Membuat sekelompok partikel ledakan yang menyebar secara radial dari titik (x, y).
    """
    try:
        count = int(count)
        color = tuple(int(c) for c in color)
    except (TypeError, ValueError) as e:
        print(f"Warning: Invalid parameters for spawn_explosion_particles: {e}")
        return

    for _ in range(count):
        # Arah acak 360 derajat
        angle = random.uniform(0, 360)
        speed = random.uniform(speed_range[0], speed_range[1])
        velocity = pygame.Vector2(0, 1).rotate(angle) * speed
        
        # Durasi hidup partikel acak antara 0.2 hingga 0.6 detik
        duration = random.uniform(0.2, 0.6)
        # Radius maksimal acak
        max_radius = random.uniform(2.0, 5.0)

        Particle(x, y, velocity, color, duration, max_radius)


def spawn_thrust_particles(x: float, y: float, direction: pygame.Vector2, color: tuple[int, int, int]):
    """
    Membuat partikel dorongan mesin yang keluar di arah berlawanan dari pergerakan kapal.
    """
    try:
        # Arah berlawanan dengan sedikit deviasi sudut
        opp_dir = -pygame.Vector2(direction)
        angle_dev = random.uniform(-15, 15)
        velocity = opp_dir.rotate(angle_dev) * random.uniform(100.0, 200.0)
        
        duration = random.uniform(0.1, 0.3)
        max_radius = random.uniform(1.5, 3.5)

        Particle(x, y, velocity, color, duration, max_radius)
    except Exception as e:
        print(f"Warning: Failed to spawn thrust particles: {e}")
