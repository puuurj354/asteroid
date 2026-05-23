"""
sounds.py — SoundManager

Menghasilkan suara synth secara programatik menggunakan array PCM murni
(pure Python + array bawaan, tidak memerlukan numpy).

PENTING: Panggil init_audio() SEBELUM pygame.init() di main.py.
"""
import array
import math
import random as rnd
import pygame

# Format mixer: 44100 Hz, 16-bit signed, stereo
SAMPLE_RATE  = 44100
SAMPLE_SIZE  = -16   # signed 16-bit
CHANNELS     = 2     # stereo
BUFFER_SIZE  = 512


def init_audio() -> bool:
    """
    Pre-inisialisasi mixer. Harus dipanggil SEBELUM pygame.init().
    Kembalikan True jika berhasil.
    """
    try:
        pygame.mixer.pre_init(SAMPLE_RATE, SAMPLE_SIZE, CHANNELS, BUFFER_SIZE)
        return True
    except Exception as e:
        print(f"Warning: Audio pre-init gagal: {e}")
        return False


# ---------------------------------------------------------------------------
# Internal PCM generation helpers
# ---------------------------------------------------------------------------

def _make_stereo_buf(num_samples: int) -> array.array:
    """Buat buffer stereo 16-bit signed, diisi nol."""
    return array.array("h", [0] * (num_samples * CHANNELS))


def _apply_envelope(
    buf: array.array,
    num_samples: int,
    attack: float = 0.05,
    release: float = 0.25,
) -> array.array:
    """Terapkan envelope attack-release (in-place)."""
    a_n = int(num_samples * attack)
    r_n = int(num_samples * release)
    for i in range(num_samples):
        if i < a_n:
            env = i / max(1, a_n)
        elif i >= num_samples - r_n:
            env = (num_samples - i) / max(1, r_n)
        else:
            env = 1.0
        idx = i * CHANNELS
        buf[idx]     = int(buf[idx]     * env)
        buf[idx + 1] = int(buf[idx + 1] * env)
    return buf


def _sweep_tone(
    freq_start: float,
    freq_end: float,
    duration_ms: int,
    volume: float = 0.4,
    wave: str = "sine",
    attack: float = 0.05,
    release: float = 0.3,
) -> "pygame.mixer.Sound | None":
    """Nada tunggal dengan frekuensi sweep."""
    try:
        n = int(SAMPLE_RATE * duration_ms / 1000)
        buf = _make_stereo_buf(n)
        peak = int(volume * 32767)
        for i in range(n):
            t = i / SAMPLE_RATE
            progress = i / max(1, n - 1)
            freq = freq_start + (freq_end - freq_start) * progress
            if wave == "square":
                raw = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            elif wave == "sawtooth":
                raw = 2.0 * (t * freq - math.floor(t * freq + 0.5))
            else:  # sine (default)
                raw = math.sin(2 * math.pi * freq * t)
            val = max(-32767, min(32767, int(peak * raw)))
            buf[i * CHANNELS]     = val
            buf[i * CHANNELS + 1] = val
        _apply_envelope(buf, n, attack, release)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception as e:
        print(f"Warning: _sweep_tone gagal: {e}")
        return None


def _noise_burst(
    freq_base: float,
    duration_ms: int,
    volume: float = 0.35,
    noise_ratio: float = 0.6,
) -> "pygame.mixer.Sound | None":
    """Ledakan noise: campuran sine bass + white noise."""
    try:
        n = int(SAMPLE_RATE * duration_ms / 1000)
        buf = _make_stereo_buf(n)
        peak = int(volume * 32767)
        for i in range(n):
            t = i / SAMPLE_RATE
            sine  = math.sin(2 * math.pi * freq_base * t)
            noise = rnd.uniform(-1.0, 1.0)
            raw   = (1 - noise_ratio) * sine + noise_ratio * noise
            val   = max(-32767, min(32767, int(peak * raw)))
            buf[i * CHANNELS]     = val
            buf[i * CHANNELS + 1] = val
        _apply_envelope(buf, n, attack=0.01, release=0.55)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception as e:
        print(f"Warning: _noise_burst gagal: {e}")
        return None


def _arpeggio(
    freqs: list[float],
    note_ms: int,
    volume: float = 0.3,
) -> "pygame.mixer.Sound | None":
    """Urutan nada (arpeggio) dalam satu buffer."""
    try:
        note_n  = int(SAMPLE_RATE * note_ms / 1000)
        total_n = note_n * len(freqs)
        buf     = _make_stereo_buf(total_n)
        peak    = int(volume * 32767)
        for note_idx, freq in enumerate(freqs):
            offset = note_idx * note_n
            for i in range(note_n):
                t   = i / SAMPLE_RATE
                a_n = max(1, int(note_n * 0.08))
                r_n = max(1, int(note_n * 0.25))
                if i < a_n:
                    env = i / a_n
                elif i >= note_n - r_n:
                    env = (note_n - i) / r_n
                else:
                    env = 1.0
                val = max(-32767, min(32767, int(peak * env * math.sin(2 * math.pi * freq * t))))
                idx = (offset + i) * CHANNELS
                buf[idx]     = val
                buf[idx + 1] = val
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception as e:
        print(f"Warning: _arpeggio gagal: {e}")
        return None


# ---------------------------------------------------------------------------
# SoundManager
# ---------------------------------------------------------------------------

class SoundManager:
    """
    Mengelola seluruh suara game yang dihasilkan secara programatik.

    Cara pakai:
        sounds = SoundManager()          # setelah pygame.init()
        sounds.play("shoot")
        sounds.toggle_mute()
    """

    def __init__(self):
        self._sounds: dict[str, "pygame.mixer.Sound | None"] = {}
        self.muted        = False
        self._initialized = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._initialized = True
            self._generate_all()
        except Exception as e:
            print(f"Warning: SoundManager tidak dapat diinisialisasi: {e}. Audio dinonaktifkan.")

    def _generate_all(self):
        """Pre-generate semua suara satu kali saat startup."""
        defs: dict[str, callable] = {
            # Senjata
            "shoot":         lambda: _sweep_tone(880, 440,  80, volume=0.28, release=0.6),
            "shoot_homing":  lambda: _sweep_tone(1100, 550, 100, volume=0.28, wave="square", release=0.5),
            # Ledakan
            "explosion_small": lambda: _noise_burst(120, 180, volume=0.32, noise_ratio=0.70),
            "explosion_large": lambda: _noise_burst(55,  400, volume=0.48, noise_ratio=0.62),
            # UFO
            "ufo_destroy":   lambda: _noise_burst(190, 280, volume=0.38, noise_ratio=0.52),
            # Powerup
            "powerup":       lambda: _arpeggio([440, 554, 659], note_ms=95,  volume=0.28),
            # Level-up fanfare
            "level_up":      lambda: _arpeggio([330, 415, 494, 659], note_ms=115, volume=0.33),
            # Bom
            "bomb":          lambda: _noise_burst(38, 580, volume=0.58, noise_ratio=0.42),
            # Game Over — arpeggio turun
            "game_over":     lambda: _arpeggio([330, 262, 220, 196], note_ms=175, volume=0.38),
            # Combo naik level
            "combo_up":      lambda: _sweep_tone(550, 880, 110, volume=0.22, release=0.4),
        }

        for name, fn in defs.items():
            try:
                self._sounds[name] = fn()
            except Exception as e:
                print(f"Warning: Gagal membuat suara '{name}': {e}")
                self._sounds[name] = None

    # ------------------------------------------------------------------
    def play(self, sound_name: str, volume_scale: float = 1.0):
        """Mainkan suara. Diam jika muted atau suara tidak tersedia."""
        if self.muted or not self._initialized:
            return
        sound = self._sounds.get(sound_name)
        if sound is None:
            return
        try:
            sound.set_volume(max(0.0, min(1.0, float(volume_scale))))
            sound.play()
        except Exception as e:
            print(f"Warning: Gagal memutar suara '{sound_name}': {e}")

    def toggle_mute(self) -> bool:
        """Toggle mute. Kembalikan state muted yang baru."""
        self.muted = not self.muted
        return self.muted
