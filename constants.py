SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_RADIUS = 20
LINE_WIDTH = 2
PLAYER_TURN_SPEED = 300
PLAYER_SPEED = 200
ASTEROID_MIN_RADIUS = 20
ASTEROID_KINDS = 3
ASTEROID_SPAWN_RATE_SECONDS = 0.8
ASTEROID_MAX_RADIUS = ASTEROID_MIN_RADIUS * ASTEROID_KINDS
SHOT_RADIUS = 5
PLAYER_SHOOT_SPEED = 500
PLAYER_SHOOT_COOLDOWN_SECONDS = 0.3

# Konfigurasi Baru
PLAYER_LIVES = 3
PLAYER_RESPAWN_COOLDOWN = 2.0
SHOT_LIFETIME = 1.5

# Fisika Kapal
PLAYER_ACCELERATION = 400.0
PLAYER_DRAG = 1.2
PLAYER_MAX_SPEED = 350.0

# Skema Warna Neon Cyber-Theme
COLOR_BG = (10, 10, 18)        # Biru gelap hampir hitam
COLOR_PLAYER = (0, 240, 255)    # Cyan neon
COLOR_ASTEROID = (80, 255, 120) # Hijau neon standar untuk asteroid biasa
COLOR_SHOT = (0, 255, 200)      # Tosca neon
COLOR_HUD = (230, 230, 250)     # Putih keperakan
COLOR_PARTICLE = (255, 170, 0)  # Orange neon
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_MUTED = (120, 120, 150)
COLOR_PAUSE = (255, 220, 0)     # Kuning neon
COLOR_UFO = (235, 50, 255)      # Ungu/Pink neon
COLOR_ENEMY_SHOT = (255, 120, 0) # Orange neon

# Warna Variasi
COLOR_CRYSTAL = (255, 0, 180)    # Pink/Magenta neon terang
COLOR_MAGNETIC = (255, 165, 0)   # Orange/Kuning neon terang
COLOR_UFO_SCOUT = (180, 0, 255)  # Ungu neon
COLOR_UFO_HUNTER = (255, 30, 30) # Merah neon

# Parameter Magnetik Asteroid
MAGNETIC_INFLUENCE_RADIUS = 220.0
MAGNETIC_PULL_FORCE = 120.0

# Konfigurasi Fitur Baru
POWERUP_DROP_CHANCE = 0.15
UFO_SPAWN_MIN_SECONDS = 15.0
UFO_SPAWN_MAX_SECONDS = 25.0

# Konfigurasi Bom
PLAYER_START_BOMBS = 2
COLOR_BOMB = (200, 255, 255)

# Sistem Combo & Multiplier
COMBO_TIMEOUT = 3.0
# Format: (min_kills_in_combo, multiplier)
# Diperiksa dari atas ke bawah — threshold tertinggi dulu
COMBO_THRESHOLDS = [(7, 8), (4, 4), (2, 2), (0, 1)]
