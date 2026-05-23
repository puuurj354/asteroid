# pyrefly: ignore [missing-import]
import pygame

from circleshape import CircleShape
from constants import (
    LINE_WIDTH,
    PLAYER_RADIUS,
    PLAYER_SHOOT_COOLDOWN_SECONDS,
    PLAYER_SHOOT_SPEED,
    PLAYER_ACCELERATION,
    PLAYER_DRAG,
    PLAYER_MAX_SPEED,
    PLAYER_TURN_SPEED,
    COLOR_PLAYER,
    COLOR_PARTICLE,
    COLOR_SHOT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PLAYER_START_BOMBS,
)
from shot import Shot
from particles import spawn_thrust_particles


class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0
        self.shoot_cooldown = 0
        self.invulnerability_timer = 0.0
        self.velocity = pygame.Vector2(0, 0)
        self.bombs = PLAYER_START_BOMBS
        # Tambahan state untuk powerup
        self.shield_active = False
        self.triple_shot_timer = 0.0
        self.rapid_fire_timer = 0.0

    def trigger_bomb(self) -> bool:
        """
        Memicu peledakan bom jika pemain memiliki bom tersisa secara defensif.
        """
        try:
            if self.bombs > 0:
                self.bombs -= 1
                return True
        except Exception as e:
            print(f"Error triggering bomb: {e}")
        return False

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def draw(self, screen):
        # Kedipan efek kekebalan (i-frames)
        if self.invulnerability_timer > 0:
            if int(self.invulnerability_timer * 10) % 2 == 0:
                # Tetap gambar tameng jika aktif demi kejelasan visual
                if self.shield_active:
                    self._draw_shield(screen)
                return

        pygame.draw.polygon(screen, COLOR_PLAYER, self.triangle(), LINE_WIDTH)

        # Gambar tameng jika aktif
        if self.shield_active:
            self._draw_shield(screen)

    def _draw_shield(self, screen):
        """
        Fungsi pembantu untuk menggambar pelindung neon berputar secara defensif.
        """
        try:
            shield_radius = self.radius + 8
            # Lingkaran dalam tameng
            pygame.draw.circle(screen, (0, 180, 255), self.position, shield_radius, 1)
            # Lingkaran luar tameng
            pygame.draw.circle(screen, (0, 240, 255), self.position, shield_radius + 4, 1)

            # Titik-titik energi neon yang berputar di sekeliling tameng
            ticks = pygame.time.get_ticks()
            angle_offset = (ticks / 8) % 360
            for i in range(4):
                dash_angle = angle_offset + i * 90
                dash_pos = self.position + pygame.Vector2(0, shield_radius + 2).rotate(dash_angle)
                pygame.draw.circle(screen, (200, 255, 255), (int(dash_pos.x), int(dash_pos.y)), 3)
        except Exception as e:
            print(f"Error drawing player shield: {e}")

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def move(self, dt):
        """
        Menambahkan gaya akselerasi maju ke velocity.
        """
        if dt <= 0:
            return
        try:
            unit_vector = pygame.Vector2(0, 1)
            rotated_vector = unit_vector.rotate(self.rotation)
            # Menambah kecepatan secara dinamis (akselerasi)
            self.velocity += rotated_vector * PLAYER_ACCELERATION * dt

            # Munculkan partikel dorongan mesin saat bergerak maju
            spawn_thrust_particles(
                self.position.x - rotated_vector.x * self.radius,
                self.position.y - rotated_vector.y * self.radius,
                rotated_vector,
                COLOR_PARTICLE
            )
        except Exception as e:
            print(f"Error in player move: {e}")

    def move_backward(self, dt):
        """
        Menambahkan gaya akselerasi mundur (rem) yang lebih lemah ke velocity.
        """
        if dt <= 0:
            return
        try:
            unit_vector = pygame.Vector2(0, 1)
            rotated_vector = unit_vector.rotate(self.rotation)
            # Hambatan rem mundur 50% dari kekuatan maju
            self.velocity -= rotated_vector * (PLAYER_ACCELERATION * 0.5) * dt
        except Exception as e:
            print(f"Error in player move_backward: {e}")

    def shoot(self):
        if self.shoot_cooldown > 0:
            return

        # Efek Rapid Fire mengurangi cooldown menembak secara drastis
        cooldown = PLAYER_SHOOT_COOLDOWN_SECONDS
        if self.rapid_fire_timer > 0:
            cooldown = 0.09  # Laju tembakan super cepat!

        self.shoot_cooldown = cooldown

        try:
            # Efek Triple Shot menembakkan 3 peluru sekaligus dalam sudut menyebar
            if self.triple_shot_timer > 0:
                angles = [-15.0, 0.0, 15.0]
                for angle in angles:
                    shot = Shot(self.position.x, self.position.y, color=COLOR_SHOT)
                    shot_vector = pygame.Vector2(0, 1)
                    rotated_shot_vector = shot_vector.rotate(self.rotation + angle)
                    shot.velocity = rotated_shot_vector * PLAYER_SHOOT_SPEED
            else:
                # Tembakan biasa
                shot = Shot(self.position.x, self.position.y, color=COLOR_SHOT)
                shot_vector = pygame.Vector2(0, 1)
                rotated_shot_vector = shot_vector.rotate(self.rotation)
                shot.velocity = rotated_shot_vector * PLAYER_SHOOT_SPEED
        except Exception as e:
            print(f"Error spawning player shot: {e}")

    def update(self, dt):
        self.shoot_cooldown -= dt
        
        # Perbarui timer kekebalan dan powerup secara defensif
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= dt
        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= dt
        if self.rapid_fire_timer > 0:
            self.rapid_fire_timer -= dt

        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.rotate(-dt)
        if keys[pygame.K_d]:
            self.rotate(dt)
        if keys[pygame.K_w]:
            self.move(dt)
        if keys[pygame.K_s]:
            self.move_backward(dt)
        if keys[pygame.K_SPACE]:
            self.shoot()

        # Terapkan gesekan (drag) luar angkasa
        if self.velocity.length_squared() > 0:
            try:
                self.velocity -= self.velocity * PLAYER_DRAG * dt
            except Exception:
                pass

        # Batasi kecepatan maksimum kapal
        try:
            if self.velocity.length() > PLAYER_MAX_SPEED:
                self.velocity = self.velocity.normalize() * PLAYER_MAX_SPEED
        except Exception:
            pass

        # Perbarui posisi kapal berdasarkan kecepatannya
        self.position += self.velocity * dt

        # Screen wrapping agar kapal tidak keluar area layar
        margin = self.radius
        if self.position.x < -margin:
            self.position.x = SCREEN_WIDTH + margin
        elif self.position.x > SCREEN_WIDTH + margin:
            self.position.x = -margin

        if self.position.y < -margin:
            self.position.y = SCREEN_HEIGHT + margin
        elif self.position.y > SCREEN_HEIGHT + margin:
            self.position.y = -margin



