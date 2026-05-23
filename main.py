import sys
import os
# pyrefly: ignore [missing-import]
import pygame
import random
import math

from asteroid import Asteroid
from asteroidfield import AsteroidField
from constants import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    COLOR_BG,
    COLOR_PLAYER,
    COLOR_ASTEROID,
    COLOR_SHOT,
    COLOR_HUD,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_PAUSE,
    COLOR_UFO,
    COLOR_ENEMY_SHOT,
    POWERUP_DROP_CHANCE,
    UFO_SPAWN_MIN_SECONDS,
    UFO_SPAWN_MAX_SECONDS,
    PLAYER_LIVES,
    PLAYER_RESPAWN_COOLDOWN,
    ASTEROID_MIN_RADIUS,
    COLOR_BOMB,
    COMBO_TIMEOUT,
    COMBO_THRESHOLDS,
)
from logger import log_event, log_state
from player import Player
from shot import Shot
from starfield import Starfield
from particles import Particle, spawn_explosion_particles
from powerup import Powerup
from ufo import UFO
from floating_text import FloatingText
from sounds import SoundManager, init_audio
from leaderboard import (
    load_leaderboard,
    save_leaderboard,
    qualifies_for_leaderboard,
    insert_score,
)


def load_high_score() -> int:
    """
    Memuat skor tertinggi dari file secara defensif.
    """
    try:
        if os.path.exists("highscore.txt"):
            with open("highscore.txt", "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
    except Exception as e:
        print(f"Warning: Failed to load high score: {e}")
    return 0


def save_high_score(score: int):
    """
    Menyimpan skor tertinggi ke file secara defensif.
    """
    try:
        with open("highscore.txt", "w") as f:
            f.write(str(score))
    except Exception as e:
        print(f"Error: Failed to save high score: {e}")


def draw_text(screen: pygame.Surface, text: str, size: int, color: tuple[int, int, int], x: float, y: float, align_center: bool = True):
    """
    Menggambar teks di layar secara defensif.
    """
    if not isinstance(screen, pygame.Surface):
        return

    try:
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align_center:
            text_rect.center = (int(x), int(y))
        else:
            text_rect.topleft = (int(x), int(y))
        screen.blit(text_surface, text_rect)
    except Exception as e:
        print(f"Error rendering text '{text}': {e}")


def get_multiplier(combo: int) -> int:
    """
    Hitung score multiplier berdasarkan jumlah kill beruntun.
    COMBO_THRESHOLDS diurutkan dari terbesar ke terkecil.
    """
    for min_combo, mult in COMBO_THRESHOLDS:
        if combo >= min_combo:
            return mult
    return 1


def get_combo_color(multiplier: int) -> tuple[int, int, int]:
    """Warna HUD teks combo berdasarkan tier multiplier."""
    if multiplier >= 8:
        return (255, 60,  60)   # Merah neon — max
    if multiplier >= 4:
        return (255, 140,  0)   # Oranye neon
    if multiplier >= 2:
        return (255, 220,  0)   # Kuning neon
    return (190, 190, 210)      # Abu-abu — tidak ada combo


def main():
    # Inisialisasi audio SEBELUM pygame.init() (diperlukan oleh pygame.mixer.pre_init)
    init_audio()

    # Inisialisasi Pygame secara defensif
    try:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
    except Exception as e:
        print(f"Critical Error: Failed to initialize Pygame: {e}")
        sys.exit(1)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Neon Asteroids")

    clock = pygame.time.Clock()
    dt = 0

    # Sprite Groups
    updatable      = pygame.sprite.Group()
    drawable       = pygame.sprite.Group()
    asteroids      = pygame.sprite.Group()
    shots          = pygame.sprite.Group()
    powerups       = pygame.sprite.Group()
    ufos           = pygame.sprite.Group()
    ufo_shots      = pygame.sprite.Group()
    floating_texts = pygame.sprite.Group()   # popup skor mengambang

    # Assign sprite containers
    Player.containers        = (updatable, drawable)
    Asteroid.containers      = (asteroids, drawable)
    AsteroidField.containers = (updatable,)
    Shot.containers          = (shots, updatable, drawable)
    Particle.containers      = (updatable, drawable)
    Powerup.containers       = (powerups, updatable, drawable)
    # UFO TIDAK dimasukkan ke updatable — hanya diupdate via loop manual
    # agar tidak terjadi double-update (pernah menyebabkan kecepatan 2x lipat)
    UFO.containers           = (ufos, drawable)
    FloatingText.containers  = (floating_texts, updatable, drawable)

    # Inisialisasi Starfield, SoundManager, & variabel game
    starfield          = Starfield(150)
    sounds             = SoundManager()
    high_score         = load_high_score()
    leaderboard_entries = load_leaderboard()
    score  = 0
    level  = 1
    lives  = PLAYER_LIVES
    state  = "MENU"  # MENU, PLAYING, PAUSED, GAME_OVER, NAME_INPUT

    player        = None
    asteroid_field = None
    input_name    = []   # buffer input 3 huruf untuk leaderboard

    # Efek getaran layar dan timer baru
    shake_timer      = 0.0
    shake_intensity  = 0.0
    level_up_timer   = 0.0
    combo_count      = 0      # jumlah kill dalam combo berjalan
    combo_timer      = 0.0    # countdown reset combo
    ufo_spawn_timer  = random.uniform(UFO_SPAWN_MIN_SECONDS, UFO_SPAWN_MAX_SECONDS)
    game_surface     = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bomb_effect_timer = 0.0
    bomb_effect_pos   = pygame.Vector2(0, 0)

    def trigger_shake(duration, intensity):
        nonlocal shake_timer, shake_intensity
        shake_timer    = max(0.0, float(duration))
        shake_intensity = max(0.0, float(intensity))

    def trigger_game_over():
        """Tangani game over: simpan skor, alihkan ke NAME_INPUT atau GAME_OVER."""
        nonlocal state, high_score
        log_event("game_over", final_score=score)
        sounds.play("game_over")
        if score > high_score:
            high_score = score
            save_high_score(high_score)
        if qualifies_for_leaderboard(score, leaderboard_entries) and score > 0:
            input_name.clear()
            state = "NAME_INPUT"
        else:
            state = "GAME_OVER"
        if player is not None:
            player.kill()

    def start_new_game():
        nonlocal player, asteroid_field, score, level, lives, state
        nonlocal ufo_spawn_timer, shake_timer, shake_intensity, level_up_timer
        nonlocal bomb_effect_timer, bomb_effect_pos, combo_count, combo_timer
        updatable.empty()
        drawable.empty()
        asteroids.empty()
        shots.empty()
        powerups.empty()
        ufos.empty()
        ufo_shots.empty()
        floating_texts.empty()

        player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        asteroid_field = AsteroidField()
        asteroid_field.level = level
        score         = 0
        level         = 1
        lives         = PLAYER_LIVES
        state         = "PLAYING"
        combo_count   = 0
        combo_timer   = 0.0
        ufo_spawn_timer  = random.uniform(UFO_SPAWN_MIN_SECONDS, UFO_SPAWN_MAX_SECONDS)
        shake_timer      = 0.0
        shake_intensity  = 0.0
        level_up_timer   = 0.0
        bomb_effect_timer = 0.0
        bomb_effect_pos   = pygame.Vector2(0, 0)
        log_event("game_started")

    while True:
        log_state()

        # 1. Menangani Event Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if state == "MENU":
                    if event.key == pygame.K_RETURN:
                        start_new_game()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                elif state == "PLAYING":
                    if event.key == pygame.K_ESCAPE:
                        state = "PAUSED"
                        log_event("game_paused")
                    elif event.key == pygame.K_m:
                        is_muted = sounds.toggle_mute()
                        log_event("audio_toggled", muted=is_muted)
                    elif event.key == pygame.K_b or event.key == pygame.K_LSHIFT:
                        if player is not None and player.alive():
                            if player.trigger_bomb():
                                trigger_shake(0.7, 25.0)
                                bomb_effect_pos   = pygame.Vector2(player.position.x, player.position.y)
                                bomb_effect_timer = 0.4
                                sounds.play("bomb")
                                log_event("bomb_triggered", bombs_left=player.bombs)

                                for shot in list(ufo_shots):
                                    shot.kill()

                                for ufo in list(ufos):
                                    spawn_explosion_particles(ufo.position.x, ufo.position.y, 20, ufo.color, (80.0, 200.0))
                                    mult  = get_multiplier(combo_count)
                                    pts   = 200 * mult
                                    score += pts
                                    combo_count += 1
                                    combo_timer  = COMBO_TIMEOUT
                                    FloatingText(ufo.position.x, ufo.position.y,
                                                 f"+{pts}" if mult == 1 else f"+{pts} ×{mult}",
                                                 get_combo_color(mult))
                                    ufo.kill()

                                for asteroid in list(asteroids):
                                    asteroid.split()

                                # Cek naik level setelah skor bertambah
                                new_level = (score // 1000) + 1
                                if new_level > level:
                                    level = new_level
                                    if asteroid_field is not None:
                                        asteroid_field.level = level
                                    level_up_timer = 2.0
                                    sounds.play("level_up")
                                    log_event("level_up", level=level)

                elif state == "PAUSED":
                    if event.key == pygame.K_ESCAPE:
                        state = "PLAYING"
                        log_event("game_resumed")
                    elif event.key == pygame.K_m:
                        sounds.toggle_mute()
                    elif event.key == pygame.K_q:
                        # Reset game state sebelum kembali ke menu utama
                        updatable.empty()
                        drawable.empty()
                        asteroids.empty()
                        shots.empty()
                        powerups.empty()
                        ufos.empty()
                        ufo_shots.empty()
                        floating_texts.empty()
                        player = None
                        asteroid_field = None
                        state = "MENU"
                        log_event("returned_to_menu")

                elif state == "GAME_OVER":
                    if event.key == pygame.K_RETURN:
                        start_new_game()
                    elif event.key == pygame.K_ESCAPE:
                        updatable.empty()
                        drawable.empty()
                        asteroids.empty()
                        shots.empty()
                        powerups.empty()
                        ufos.empty()
                        ufo_shots.empty()
                        floating_texts.empty()
                        player = None
                        asteroid_field = None
                        state = "MENU"

                elif state == "NAME_INPUT":
                    if event.key == pygame.K_BACKSPACE:
                        if input_name:
                            input_name.pop()
                    elif event.key == pygame.K_RETURN:
                        if input_name:
                            name = "".join(input_name).ljust(3, "_")
                        else:
                            name = "___"
                        leaderboard_entries[:] = insert_score(name, score, leaderboard_entries)
                        save_leaderboard(leaderboard_entries)
                        state = "MENU"
                    elif len(input_name) < 3:
                        if pygame.K_a <= event.key <= pygame.K_z:
                            input_name.append(chr(event.key).upper())

        # 2. Pembaruan State Game (Update)
        if state == "PLAYING":
            # Perbarui timer secara defensif
            if level_up_timer > 0:
                level_up_timer -= dt
            if shake_timer > 0:
                shake_timer -= dt
            else:
                shake_intensity = 0.0

            if bomb_effect_timer > 0:
                bomb_effect_timer -= dt
                if bomb_effect_timer < 0:
                    bomb_effect_timer = 0.0

            # Perbarui timer combo — reset jika tidak ada kill dalam COMBO_TIMEOUT detik
            if combo_timer > 0:
                combo_timer -= dt
                if combo_timer <= 0:
                    combo_count = 0
                    combo_timer = 0.0

            # Spawn UFO Musuh secara berkala
            ufo_spawn_timer -= dt
            if ufo_spawn_timer <= 0:
                try:
                    UFO() # ditambahkan otomatis via containers
                except Exception as e:
                    print(f"Error spawning UFO: {e}")
                ufo_spawn_timer = random.uniform(UFO_SPAWN_MIN_SECONDS, UFO_SPAWN_MAX_SECONDS)

            # Perbarui semua sprite dalam group (kecuali asteroid yang diupdate manual di bawah)
            updatable.update(dt)

            # Perbarui asteroid secara manual agar referensi player dapat dilewatkan untuk tarikan magnet
            for asteroid in asteroids:
                try:
                    asteroid.update(dt, player)
                except Exception as e:
                    print(f"Error updating asteroid: {e}")

            # Perbarui UFO untuk bergerak dan menembak secara defensif
            for ufo in ufos:
                try:
                    target = player.position if player is not None else pygame.Vector2(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
                    new_enemy_shots = ufo.update(dt, target, level)
                    
                    for enemy_shot in new_enemy_shots:
                        ufo_shots.add(enemy_shot)
                except Exception as e:
                    print(f"Error processing UFO actions: {e}")

            # Efek partikel jejak peluru (Shot Trails)
            for shot in shots:
                try:
                    Particle(shot.position.x, shot.position.y, pygame.Vector2(0, 0), shot.color, 0.12, 2.5)
                except Exception:
                    pass
            for enemy_shot in ufo_shots:
                try:
                    Particle(enemy_shot.position.x, enemy_shot.position.y, pygame.Vector2(0, 0), enemy_shot.color, 0.12, 2.5)
                except Exception:
                    pass

            # Cek Tabrakan: Asteroid vs Tembakan Player
            for asteroid in list(asteroids):
                for shot in list(shots):
                    if not getattr(shot, "is_enemy", False) and asteroid.collides_with(shot):
                        log_event("asteroid_shot")
                        trigger_shake(0.2, 4.0 if asteroid.radius > ASTEROID_MIN_RADIUS * 2 else 2.0)

                        # Tentukan skor dasar berdasarkan ukuran asteroid
                        if asteroid.radius > ASTEROID_MIN_RADIUS * 2:
                            base_pts = 20
                        elif asteroid.radius > ASTEROID_MIN_RADIUS:
                            base_pts = 50
                        else:
                            base_pts = 100
                            # Peluang spawn power-up dari asteroid kecil
                            if random.random() < POWERUP_DROP_CHANCE:
                                try:
                                    kind = random.choice(["shield", "triple", "rapid", "bomb", "homing", "speed"])
                                    Powerup(asteroid.position.x, asteroid.position.y, kind)
                                except Exception as e:
                                    print(f"Error spawning Powerup: {e}")

                        # Terapkan combo multiplier
                        combo_count += 1
                        combo_timer  = COMBO_TIMEOUT
                        mult = get_multiplier(combo_count)
                        pts  = base_pts * mult
                        score += pts

                        # Spawn floating score popup
                        popup_text  = f"+{pts}" if mult == 1 else f"+{pts} ×{mult}"
                        popup_color = get_combo_color(mult)
                        FloatingText(asteroid.position.x, asteroid.position.y - 10, popup_text, popup_color)

                        # Suara ledakan asteroid
                        sounds.play("explosion_small")
                        if mult > combo_count - 1 and combo_count in (2, 4, 7):
                            sounds.play("combo_up")  # ding saat naik tier

                        # Tingkatkan level setiap 1000 poin
                        new_level = (score // 1000) + 1
                        if new_level > level:
                            level = new_level
                            if asteroid_field is not None:
                                asteroid_field.level = level
                            level_up_timer = 2.0
                            sounds.play("level_up")
                            log_event("level_up", level=level)

                        asteroid.split()
                        shot.kill()

            # Cek Tabrakan: Tembakan Player vs UFO
            for shot in list(shots):
                if not getattr(shot, "is_enemy", False):
                    for ufo in list(ufos):
                        if shot.collides_with(ufo):
                            log_event("ufo_destroyed")
                            spawn_explosion_particles(ufo.position.x, ufo.position.y, 20, ufo.color, (80.0, 200.0))
                            trigger_shake(0.35, 8.0)

                            # Terapkan combo multiplier ke skor UFO
                            combo_count += 1
                            combo_timer  = COMBO_TIMEOUT
                            mult  = get_multiplier(combo_count)
                            pts   = 200 * mult
                            score += pts

                            FloatingText(ufo.position.x, ufo.position.y,
                                         f"+{pts}" if mult == 1 else f"+{pts} ×{mult}",
                                         get_combo_color(mult))
                            sounds.play("ufo_destroy")

                            if random.random() < 0.35:
                                try:
                                    kind = random.choice(["shield", "triple", "rapid", "bomb", "homing", "speed"])
                                    Powerup(ufo.position.x, ufo.position.y, kind)
                                except Exception as e:
                                    print(f"Error spawning Powerup: {e}")

                            shot.kill()
                            ufo.kill()

            # Cek Tabrakan: Player vs Power-up
            for powerup in list(powerups):
                if player is not None and player.collides_with(powerup):
                    log_event("powerup_collected", kind=powerup.kind)
                    spawn_explosion_particles(powerup.position.x, powerup.position.y, 12, powerup.color, (60.0, 160.0))
                    trigger_shake(0.15, 3.0)
                    sounds.play("powerup")

                    if powerup.kind == "shield":
                        player.shield_active = True
                    elif powerup.kind == "triple":
                        player.triple_shot_timer = 8.0
                    elif powerup.kind == "rapid":
                        player.rapid_fire_timer = 8.0
                    elif powerup.kind == "bomb":
                        player.bombs = min(5, player.bombs + 1)
                    elif powerup.kind == "homing":
                        player.homing_timer  = 7.0
                        player.homing_groups = (asteroids, ufos)
                    elif powerup.kind == "speed":
                        player.speed_timer = 5.0

                    powerup.kill()

            # Cek Tabrakan: Asteroid vs Pemain
            if player is not None and player.invulnerability_timer <= 0:
                for asteroid in list(asteroids):
                    if asteroid.collides_with(player):
                        log_event("player_hit")

                        if player.shield_active:
                            player.shield_active = False
                            player.invulnerability_timer = 1.0
                            spawn_explosion_particles(player.position.x, player.position.y, 25, (0, 240, 255), (100.0, 250.0))
                            trigger_shake(0.35, 10.0)
                            asteroid.split()
                        else:
                            spawn_explosion_particles(player.position.x, player.position.y, 35, COLOR_PLAYER, (120.0, 320.0))
                            trigger_shake(0.6, 20.0)
                            lives -= 1
                            if lives > 0:
                                player.position = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                                player.velocity = pygame.Vector2(0, 0)
                                player.invulnerability_timer = PLAYER_RESPAWN_COOLDOWN

                                center = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                                for ast in list(asteroids):
                                    if ast.position.distance_to(center) < 250:
                                        ast.kill()
                            else:
                                trigger_game_over()

            # Cek Tabrakan: UFO vs Pemain
            if player is not None and player.invulnerability_timer <= 0:
                for ufo in list(ufos):
                    if ufo.collides_with(player):
                        log_event("player_hit_by_ufo")
                        ufo.kill()
                        spawn_explosion_particles(ufo.position.x, ufo.position.y, 25, ufo.color, (100.0, 220.0))

                        if player.shield_active:
                            player.shield_active = False
                            player.invulnerability_timer = 1.0
                            spawn_explosion_particles(player.position.x, player.position.y, 25, (0, 240, 255), (100.0, 250.0))
                            trigger_shake(0.35, 10.0)
                        else:
                            spawn_explosion_particles(player.position.x, player.position.y, 35, COLOR_PLAYER, (120.0, 320.0))
                            trigger_shake(0.6, 20.0)
                            lives -= 1
                            if lives > 0:
                                player.position = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                                player.velocity = pygame.Vector2(0, 0)
                                player.invulnerability_timer = PLAYER_RESPAWN_COOLDOWN
                            else:
                                trigger_game_over()

            # Cek Tabrakan: Tembakan UFO vs Pemain
            if player is not None and player.invulnerability_timer <= 0:
                for ufo_shot in list(ufo_shots):
                    if ufo_shot.collides_with(player):
                        log_event("player_hit_by_ufo_shot")
                        ufo_shot.kill()

                        if player.shield_active:
                            player.shield_active = False
                            player.invulnerability_timer = 1.0
                            spawn_explosion_particles(player.position.x, player.position.y, 25, (0, 240, 255), (100.0, 250.0))
                            trigger_shake(0.3, 8.0)
                        else:
                            spawn_explosion_particles(player.position.x, player.position.y, 35, COLOR_PLAYER, (120.0, 320.0))
                            trigger_shake(0.6, 20.0)
                            lives -= 1
                            if lives > 0:
                                player.position = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                                player.velocity = pygame.Vector2(0, 0)
                                player.invulnerability_timer = PLAYER_RESPAWN_COOLDOWN
                            else:
                                trigger_game_over()

        # Starfield selalu diupdate terlepas dari state game
        starfield.update(dt)

        # 3. Penggambaran Visual (Render) menggunakan game_surface
        game_surface.fill(COLOR_BG)
        
        # Gambar Starfield paling awal agar berada di latar belakang
        starfield.draw(game_surface)

        # Gambar semua sprite game (kecuali saat di main menu utama)
        if state != "MENU":
            for sprite in drawable:
                sprite.draw(game_surface)

            # Gambar efek shockwave bom
            if bomb_effect_timer > 0:
                try:
                    progress = (0.4 - bomb_effect_timer) / 0.4
                    max_radius = 1500.0
                    current_radius = progress * max_radius
                    
                    pygame.draw.circle(game_surface, COLOR_BOMB, (int(bomb_effect_pos.x), int(bomb_effect_pos.y)), int(current_radius), 3)
                    if current_radius > 40:
                        pygame.draw.circle(game_surface, (255, 255, 255), (int(bomb_effect_pos.x), int(bomb_effect_pos.y)), int(current_radius - 30), 1)
                    if current_radius > 80:
                        pygame.draw.circle(game_surface, (150, 255, 255), (int(bomb_effect_pos.x), int(bomb_effect_pos.y)), int(current_radius - 60), 1)
                except Exception as e:
                    print(f"Error drawing bomb shockwave: {e}")

        # Menggambar UI HUD (Skor, Level, Nyawa)
        if state in ["PLAYING", "PAUSED", "GAME_OVER"]:
            # Teks Skor & High Score
            draw_text(game_surface, f"SCORE: {score:04d}", 28, COLOR_HUD, 20, 20, align_center=False)
            draw_text(game_surface, f"HI-SCORE: {high_score:04d}", 28, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, 20, align_center=True)
            draw_text(game_surface, f"LEVEL: {level}", 28, COLOR_HUD, SCREEN_WIDTH - 120, 20, align_center=False)

            # Menggambar Icon Nyawa (bentuk segitiga pesawat mini)
            for i in range(lives):
                x_pos = 30 + i * 25
                y_pos = 65
                p1 = (x_pos, y_pos - 8)
                p2 = (x_pos - 6, y_pos + 6)
                p3 = (x_pos + 6, y_pos + 6)
                pygame.draw.polygon(game_surface, COLOR_PLAYER, [p1, p2, p3], 1)

            # Menggambar Icon Bom (lingkaran neon kecil bertuliskan 'B')
            if player is not None:
                bombs_count = getattr(player, "bombs", 0)
                for i in range(bombs_count):
                    x_pos = 30 + i * 28
                    y_pos = 95
                    pygame.draw.circle(game_surface, COLOR_BOMB, (x_pos, y_pos), 10, 1)
                    draw_text(game_surface, "B", 16, COLOR_BOMB, x_pos, y_pos - 1, align_center=True)

            # Menggambar indikator durasi powerup aktif
            hud_y = 60
            if player is not None:
                if player.triple_shot_timer > 0:
                    draw_text(game_surface, f"TRIPLE SHOT: {player.triple_shot_timer:.1f}s", 20, (255, 220, 0), SCREEN_WIDTH - 180, hud_y, align_center=False)
                    hud_y += 22
                if player.rapid_fire_timer > 0:
                    draw_text(game_surface, f"RAPID FIRE: {player.rapid_fire_timer:.1f}s", 20, (50, 255, 100), SCREEN_WIDTH - 180, hud_y, align_center=False)
                    hud_y += 22
                if player.homing_timer > 0:
                    draw_text(game_surface, f"HOMING: {player.homing_timer:.1f}s", 20, (255, 90, 60), SCREEN_WIDTH - 180, hud_y, align_center=False)
                    hud_y += 22
                if player.speed_timer > 0:
                    draw_text(game_surface, f"SPEED BOOST: {player.speed_timer:.1f}s", 20, (0, 210, 255), SCREEN_WIDTH - 180, hud_y, align_center=False)
                    hud_y += 22

            # Indikator mute audio
            if sounds.muted:
                draw_text(game_surface, "[MUTED]", 18, COLOR_TEXT_MUTED, SCREEN_WIDTH - 50, SCREEN_HEIGHT - 20, align_center=False)

            # Menggambar Teks Efek Level Up
            if level_up_timer > 0:
                pulse = math.sin(level_up_timer * 10) * 0.1 + 0.9
                text_size = int(48 * pulse)
                color = (255, 220, 0) if int(level_up_timer * 5) % 2 == 0 else (255, 255, 255)
                draw_text(game_surface, f"LEVEL UP: LEVEL {level}!", text_size, color, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 150)

            # Combo Multiplier display (tampil saat combo_count >= 2)
            if combo_count >= 2 and state == "PLAYING":
                mult   = get_multiplier(combo_count)
                ccolor = get_combo_color(mult)
                remaining = combo_timer / COMBO_TIMEOUT if COMBO_TIMEOUT > 0 else 0
                combo_label = f"COMBO ×{mult}  ({combo_count} KILLS)"
                draw_text(game_surface, combo_label, 24, ccolor, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 52)
                # Bar timer combo
                bar_w = 130
                bar_h = 4
                bar_x = SCREEN_WIDTH // 2 - bar_w // 2
                bar_y = SCREEN_HEIGHT - 36
                pygame.draw.rect(game_surface, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(game_surface, ccolor,       (bar_x, bar_y, int(bar_w * max(0.0, remaining)), bar_h))

        # Layar Overlay / Tampilan Khusus State
        if state == "MENU":
            # Overlay Gelap
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 5, 12, 160))
            game_surface.blit(overlay, (0, 0))

            draw_text(game_surface, "NEON ASTEROIDS", 72, COLOR_PLAYER, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100)
            draw_text(game_surface, "PRESS ENTER TO START", 32, COLOR_TEXT, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10)
            draw_text(game_surface, "PRESS ESC TO EXIT", 24, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50)

            # Petunjuk Kontrol
            draw_text(game_surface, "CONTROLS:", 24, COLOR_HUD, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 120)
            draw_text(game_surface, "W / S : MOVE FORWARD / BACKWARD", 22, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 145)
            draw_text(game_surface, "A / D : ROTATE SHIP", 22, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 165)
            draw_text(game_surface, "SPACE : SHOOT LASER", 22, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 185)
            draw_text(game_surface, "B / LSHIFT : BOMB  •  M : MUTE AUDIO", 22, COLOR_BOMB, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 205)
            draw_text(game_surface, "ESC : PAUSE GAME  •  Q : QUIT TO MENU", 22, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 225)

            # Hall of Fame (Leaderboard) di kanan atas menu
            draw_text(game_surface, "HALL OF FAME", 22, COLOR_HUD, SCREEN_WIDTH - 130, 80)
            if leaderboard_entries:
                for i, entry in enumerate(leaderboard_entries[:5]):
                    rank_color = (255, 215, 0) if i == 0 else ((220, 180, 100) if i < 3 else COLOR_TEXT_MUTED)
                    row_y = 108 + i * 26
                    draw_text(game_surface, f"#{i+1}  {entry['name']}   {entry['score']:>6}", 19, rank_color, SCREEN_WIDTH - 130, row_y)
            else:
                draw_text(game_surface, "NO SCORES YET", 19, COLOR_TEXT_MUTED, SCREEN_WIDTH - 130, 110)

        elif state == "PAUSED":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            game_surface.blit(overlay, (0, 0))

            draw_text(game_surface, "GAME PAUSED", 64, COLOR_PAUSE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)
            draw_text(game_surface, "PRESS ESC TO RESUME", 28, COLOR_TEXT, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20)
            draw_text(game_surface, "PRESS Q TO QUIT TO MENU", 24, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60)

        elif state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            game_surface.blit(overlay, (0, 0))

            draw_text(game_surface, "GAME OVER", 72, COLOR_ASTEROID, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100)
            draw_text(game_surface, f"YOUR SCORE: {score}", 36, COLOR_PLAYER, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20)
            draw_text(game_surface, f"HIGH SCORE: {high_score}", 28, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20)
            draw_text(game_surface, "PRESS ENTER TO PLAY AGAIN", 32, COLOR_TEXT, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 90)
            draw_text(game_surface, "PRESS ESC TO RETURN TO MENU", 24, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 130)

        elif state == "NAME_INPUT":
            # Overlay gelap semi-transparan
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 10, 210))
            game_surface.blit(overlay, (0, 0))

            draw_text(game_surface, "NEW HIGH SCORE!", 60, COLOR_PAUSE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 130)
            draw_text(game_surface, f"YOUR SCORE: {score}", 36, COLOR_PLAYER, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60)
            draw_text(game_surface, "ENTER YOUR NAME (3 LETTERS):", 28, COLOR_HUD, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10)

            # Tampilkan huruf yang diketik dengan efek kursor berkedip
            cursor_char = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " "
            filled      = "".join(input_name)
            remaining_n = 3 - len(input_name)
            if remaining_n > 0:
                display_name = filled + cursor_char + "_" * (remaining_n - 1)
            else:
                display_name = filled
            draw_text(game_surface, display_name, 72, COLOR_PLAYER, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 80)
            draw_text(game_surface, "PRESS ENTER TO CONFIRM", 22, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150)

        # Hitung offset getaran layar (Screen Shake) secara defensif
        offset_x = 0
        offset_y = 0
        if shake_timer > 0:
            offset_x = int(random.uniform(-shake_intensity, shake_intensity))
            offset_y = int(random.uniform(-shake_intensity, shake_intensity))

        # Blit game_surface ke layar utama dengan offset shake
        screen.fill(COLOR_BG)
        screen.blit(game_surface, (offset_x, offset_y))
        pygame.display.flip()

        # Dapatkan delta time frame berikutnya
        dt = clock.tick(60) / 1000


if __name__ == "__main__":
    main()


