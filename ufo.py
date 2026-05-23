import random
# pyrefly: ignore [missing-import]
import pygame
import math
from circleshape import CircleShape
from constants import (
    LINE_WIDTH,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_UFO_SCOUT,
    COLOR_UFO_HUNTER,
    COLOR_ENEMY_SHOT,
)
from shot import Shot


class UFO(CircleShape):
    """
    Kapal musuh Alien UFO yang sesekali muncul.
    UFO terbang melintasi layar dengan karakteristik unik berdasarkan tipenya:
    - Scout: Bergerak zigzag cepat, menembakkan laser tunggal akurat.
    - Hunter: Mengikuti koordinat Y pemain secara dinamis, menembakkan burst 2 peluru.
    """
    def __init__(self):
        # Pilih tipe UFO secara acak
        self.ufo_type = random.choice(["scout", "hunter"])
        
        # Pilih sisi kemunculan secara acak (kiri atau kanan)
        self.side = random.choice(["left", "right"])
        
        try:
            if self.side == "left":
                start_x = -30.0
                vx_base = random.uniform(90.0, 130.0)
            else:
                start_x = SCREEN_WIDTH + 30.0
                vx_base = -random.uniform(90.0, 130.0)
                
            start_y = random.uniform(150.0, SCREEN_HEIGHT - 150.0)
        except Exception:
            start_x = -30.0
            vx_base = 100.0
            start_y = SCREEN_HEIGHT / 2

        super().__init__(start_x, start_y, 20.0)
        
        # Atur warna dan kecepatan horizontal berdasarkan tipe
        if self.ufo_type == "scout":
            self.color = COLOR_UFO_SCOUT
            self.velocity = pygame.Vector2(vx_base * 1.4, 0.0)  # Lebih cepat 40%
            self.shoot_cooldown = random.uniform(0.8, 1.5)
        else:
            self.color = COLOR_UFO_HUNTER
            self.velocity = pygame.Vector2(vx_base * 0.8, 0.0)  # Lebih lambat 20%
            self.shoot_cooldown = random.uniform(1.2, 2.2)

        self.base_y = start_y
        self.time_alive = 0.0
        
        # State untuk burst fire tipe Hunter
        self.burst_shots_left = 0
        self.burst_timer = 0.0

    def draw(self, screen: pygame.Surface):
        """
        Menggambar piring terbang UFO neon sesuai tipenya secara defensif.
        """
        if not isinstance(screen, pygame.Surface):
            return

        try:
            # Titik sudut untuk membentuk badan piring terbang UFO (poligon bersudut 6)
            p1 = self.position + pygame.Vector2(-self.radius, 0.0)
            p2 = self.position + pygame.Vector2(-self.radius * 0.5, -self.radius * 0.4)
            p3 = self.position + pygame.Vector2(self.radius * 0.5, -self.radius * 0.4)
            p4 = self.position + pygame.Vector2(self.radius, 0.0)
            p5 = self.position + pygame.Vector2(self.radius * 0.6, self.radius * 0.4)
            p6 = self.position + pygame.Vector2(-self.radius * 0.6, self.radius * 0.4)
            
            # Gambar glow di bawahnya
            glow_color = tuple(max(0, c - 80) for c in self.color)
            pygame.draw.polygon(screen, glow_color, [p1, p2, p3, p4, p5, p6], LINE_WIDTH + 2)
            pygame.draw.polygon(screen, self.color, [p1, p2, p3, p4, p5, p6], LINE_WIDTH)

            # Gambar kubah kaca UFO di bagian atas
            dome_w = int(self.radius * 0.8)
            dome_h = int(self.radius * 0.8)
            dome_x = int(self.position.x - dome_w / 2)
            dome_y = int(self.position.y - self.radius * 0.6 - dome_h / 2)
            
            dome_rect = pygame.Rect(dome_x, dome_y, dome_w, dome_h)
            pygame.draw.arc(screen, self.color, dome_rect, 0, math.pi, LINE_WIDTH)

            # Tambahkan garis horizontal pemisah badan piring terbang
            pygame.draw.line(screen, self.color, p1, p4, LINE_WIDTH)

            # Detail tambahan sesuai tipe
            if self.ufo_type == "scout":
                # Gambar antena kecil di atas kubah untuk Scout
                antena_tip = self.position + pygame.Vector2(0, -self.radius * 1.3)
                antena_base = self.position + pygame.Vector2(0, -self.radius * 0.8)
                pygame.draw.line(screen, self.color, antena_base, antena_tip, 1)
                pygame.draw.circle(screen, (220, 220, 255), (int(antena_tip.x), int(antena_tip.y)), 2)
            elif self.ufo_type == "hunter":
                # Gambar lubang meriam gantung kecil di bawah Hunter
                cannon_pos = self.position + pygame.Vector2(0, self.radius * 0.55)
                pygame.draw.rect(screen, self.color, (int(cannon_pos.x - 3), int(cannon_pos.y), 6, 5), 1)

        except Exception as e:
            print(f"Error drawing UFO: {e}")

    def update(self, dt: float, player_pos: pygame.Vector2 = None, current_level: int = 1) -> list:
        """
        Perbarui posisi dan logika serangan UFO secara defensif.
        Mengembalikan list dari objek Shot baru jika menembak di frame ini.
        """
        new_shots = []
        try:
            val_dt = float(dt)
        except (TypeError, ValueError):
            val_dt = 0.0

        self.time_alive += val_dt

        # 1. Perbarui Pergerakan UFO berdasarkan tipe
        try:
            if self.ufo_type == "scout":
                # Scout: Gelombang sinus berfrekuensi tinggi (kelok-kelok tajam)
                target_y = self.base_y + math.sin(self.time_alive * 5.0) * 110.0
                self.position.x += self.velocity.x * val_dt
                self.position.y = target_y
            else:
                # Hunter: Bergerak horizontal sambil mengejar ketinggian Y player secara perlahan (hovering)
                self.position.x += self.velocity.x * val_dt
                if player_pos is not None:
                    diff_y = player_pos.y - self.position.y
                    # Kecepatan melayang vertikal
                    vertical_speed = 80.0 + (current_level - 1) * 5.0
                    if abs(diff_y) > 10.0:
                        direction_y = 1.0 if diff_y > 0 else -1.0
                        self.position.y += direction_y * vertical_speed * val_dt
        except Exception as e:
            self.position += self.velocity * val_dt
            print(f"Error updating UFO movement: {e}")

        # 2. Kurangi Cooldown Tembak & Hitung Serangan
        self.shoot_cooldown -= val_dt

        # Faktor peningkat kesulitan berdasarkan level
        cooldown_factor = max(0.4, 1.0 - (current_level - 1) * 0.08)

        if self.shoot_cooldown <= 0:
            base_cooldown = random.uniform(1.8, 3.2)
            
            if self.ufo_type == "scout":
                # Scout menembak peluru tunggal sangat cepat
                self.shoot_cooldown = base_cooldown * 0.65 * cooldown_factor
                if player_pos is not None:
                    try:
                        dir_vector = (player_pos - self.position).normalize()
                        # Tambahkan ketidakakuratan tipis
                        dir_vector = dir_vector.rotate(random.uniform(-4.0, 4.0))
                        
                        shot = Shot(self.position.x, self.position.y, radius=4, color=COLOR_ENEMY_SHOT, is_enemy=True)
                        shot.velocity = dir_vector * 340.0  # Peluru cepat
                        new_shots.append(shot)
                    except Exception as e:
                        print(f"Error creating Scout shot: {e}")
            
            elif self.ufo_type == "hunter":
                # Hunter memicu tembakan burst 2 peluru
                self.shoot_cooldown = base_cooldown * 1.15 * cooldown_factor
                self.burst_shots_left = 2
                self.burst_timer = 0.0

        # Tangani tembakan beruntun (burst fire) untuk tipe Hunter secara defensif
        if self.burst_shots_left > 0:
            self.burst_timer -= val_dt
            if self.burst_timer <= 0:
                self.burst_timer = 0.16  # Jeda singkat antar tembakan burst
                self.burst_shots_left -= 1
                if player_pos is not None:
                    try:
                        dir_vector = (player_pos - self.position).normalize()
                        dir_vector = dir_vector.rotate(random.uniform(-7.0, 7.0))
                        
                        shot = Shot(self.position.x, self.position.y, radius=4, color=COLOR_ENEMY_SHOT, is_enemy=True)
                        shot.velocity = dir_vector * 260.0
                        new_shots.append(shot)
                    except Exception as e:
                        print(f"Error creating Hunter burst shot: {e}")

        # 3. Cek jika UFO keluar batas layar untuk dihapus (despawn)
        try:
            margin = self.radius + 50.0
            if self.velocity.x > 0 and self.position.x > SCREEN_WIDTH + margin:
                self.kill()
            elif self.velocity.x < 0 and self.position.x < -margin:
                self.kill()
        except Exception:
            pass

        return new_shots

