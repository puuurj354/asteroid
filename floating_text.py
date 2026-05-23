"""
floating_text.py — FloatingText sprite

Teks skor mengambang (+100, ×4, dll.) yang muncul di posisi kill,
melayang ke atas, dan memudar secara gradual sebelum dihapus.
"""
# pyrefly: ignore [missing-import]
import pygame


class FloatingText(pygame.sprite.Sprite):
    """
    Sprite teks skor yang melayang ke atas dan memudar.

    Warna berdasarkan multiplier:
      ×1  → Abu-abu terang
      ×2  → Kuning neon
      ×4  → Oranye neon
      ×8  → Merah neon
    """

    RISE_SPEED = 55.0   # pixel/detik ke atas
    FONT_SIZE   = 22

    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        color: tuple[int, int, int],
        duration: float = 0.9,
    ):
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()

        try:
            self.pos_x    = float(x)
            self.pos_y    = float(y)
            self.text     = str(text)
            self.base_color = tuple(int(c) for c in color)[:3]
            self.duration = max(0.1, float(duration))
        except (TypeError, ValueError) as e:
            print(f"Warning: FloatingText init error: {e}. Using defaults.")
            self.pos_x     = 0.0
            self.pos_y     = 0.0
            self.text      = "?"
            self.base_color = (255, 255, 255)
            self.duration  = 0.9

        self.age = 0.0

    # ------------------------------------------------------------------
    def update(self, dt: float):
        """Naikan posisi dan tambah umur. Kill saat durasi habis."""
        try:
            dt = max(0.0, float(dt))
        except (TypeError, ValueError):
            dt = 0.0

        self.age   += dt
        self.pos_y -= self.RISE_SPEED * dt

        if self.age >= self.duration:
            self.kill()

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface):
        """Render teks dengan warna yang memudar seiring umur."""
        if not isinstance(screen, pygame.Surface):
            return

        try:
            life_ratio = min(1.0, self.age / self.duration)
            # Kurangi kecerahan warna seiring memudar
            fade = 1.0 - life_ratio * 0.85
            color = (
                max(0, int(self.base_color[0] * fade)),
                max(0, int(self.base_color[1] * fade)),
                max(0, int(self.base_color[2] * fade)),
            )

            font = pygame.font.Font(None, self.FONT_SIZE)
            surf = font.render(self.text, True, color)
            x = int(self.pos_x) - surf.get_width() // 2
            y = int(self.pos_y)
            screen.blit(surf, (x, y))
        except Exception as e:
            print(f"Error drawing FloatingText: {e}")
