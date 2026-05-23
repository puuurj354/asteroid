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
)
from logger import log_event, log_state
from player import Player
from shot import Shot
from starfield import Starfield
from particles import Particle, spawn_explosion_particles
from powerup import Powerup
from ufo import UFO


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


def main():
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
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    ufos = pygame.sprite.Group()
    ufo_shots = pygame.sprite.Group()

    # Assign sprite containers
    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, drawable)
    AsteroidField.containers = (updatable,)
    Shot.containers = (shots, updatable, drawable)
    Particle.containers = (updatable, drawable)
    Powerup.containers = (powerups, updatable, drawable)
    UFO.containers = (ufos, updatable, drawable)

    # Inisialisasi Starfield & variabel game
    starfield = Starfield(150)
    high_score = load_high_score()
    score = 0
    level = 1
    lives = PLAYER_LIVES
    state = "MENU"  # MENU, PLAYING, PAUSED, GAME_OVER

    player = None
    asteroid_field = None

    # Efek getaran layar dan timer baru
    shake_timer = 0.0
    shake_intensity = 0.0
    level_up_timer = 0.0
    ufo_spawn_timer = random.uniform(UFO_SPAWN_MIN_SECONDS, UFO_SPAWN_MAX_SECONDS)
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bomb_effect_timer = 0.0
    bomb_effect_pos = pygame.Vector2(0, 0)

    def trigger_shake(duration, intensity):
        nonlocal shake_timer, shake_intensity
        shake_timer = max(0.0, float(duration))
        shake_intensity = max(0.0, float(intensity))

    def start_new_game():
        nonlocal player, asteroid_field, score, level, lives, state
        nonlocal ufo_spawn_timer, shake_timer, shake_intensity, level_up_timer
        nonlocal bomb_effect_timer, bomb_effect_pos
        updatable.empty()
        drawable.empty()
        asteroids.empty()
        shots.empty()
        powerups.empty()
        ufos.empty()
        ufo_shots.empty()

        player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        asteroid_field = AsteroidField()
        asteroid_field.level = level
        score = 0
        level = 1
        lives = PLAYER_LIVES
        state = "PLAYING"
        ufo_spawn_timer = random.uniform(UFO_SPAWN_MIN_SECONDS, UFO_SPAWN_MAX_SECONDS)
        shake_timer = 0.0
        shake_intensity = 0.0
        level_up_timer = 0.0
        bomb_effect_timer = 0.0
        bomb_effect_pos = pygame.Vector2(0, 0)
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
                    elif event.key == pygame.K_b or event.key == pygame.K_LSHIFT:
                        if player is not None and player.alive():
                            if player.trigger_bomb():
                                trigger_shake(0.7, 25.0)
                                bomb_effect_pos = pygame.Vector2(player.position.x, player.position.y)
                                bomb_effect_timer = 0.4
                                log_event("bomb_triggered", bombs_left=player.bombs)
                                
                                for shot in list(ufo_shots):
                                    shot.kill()
                                
                                for ufo in list(ufos):
                                    spawn_explosion_particles(ufo.position.x, ufo.position.y, 20, ufo.color, (80.0, 200.0))
                                    score += 200
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
                                    log_event("level_up", level=level)

                elif state == "PAUSED":
                    if event.key == pygame.K_ESCAPE:
                        state = "PLAYING"
                        log_event("game_resumed")
                    elif event.key == pygame.K_q:
                        # Reset game state sebelum kembali ke menu utama
                        updatable.empty()
                        drawable.empty()
                        asteroids.empty()
                        shots.empty()
                        powerups.empty()
                        ufos.empty()
                        ufo_shots.empty()
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
                        player = None
                        asteroid_field = None
                        state = "MENU"

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
            for asteroid in asteroids:
                for shot in shots:
                    if not getattr(shot, "is_enemy", False) and asteroid.collides_with(shot):
                        log_event("asteroid_shot")
                        trigger_shake(0.2, 4.0 if asteroid.radius > ASTEROID_MIN_RADIUS * 2 else 2.0)

                        if asteroid.radius > ASTEROID_MIN_RADIUS * 2:
                            score += 20
                        elif asteroid.radius > ASTEROID_MIN_RADIUS:
                            score += 50
                        else:
                            score += 100
                            # Peluang spawn power-up
                            if random.random() < POWERUP_DROP_CHANCE:
                                try:
                                    kind = random.choice(["shield", "triple", "rapid"])
                                    Powerup(asteroid.position.x, asteroid.position.y, kind)
                                except Exception as e:
                                    print(f"Error spawning Powerup: {e}")

                        # Tingkatkan level setiap 1000 poin
                        new_level = (score // 1000) + 1
                        if new_level > level:
                            level = new_level
                            if asteroid_field is not None:
                                asteroid_field.level = level
                            level_up_timer = 2.0
                            log_event("level_up", level=level)

                        asteroid.split()
                        shot.kill()

            # Cek Tabrakan: Tembakan Player vs UFO
            for shot in shots:
                if not getattr(shot, "is_enemy", False):
                    for ufo in ufos:
                        if shot.collides_with(ufo):
                            log_event("ufo_destroyed")
                            spawn_explosion_particles(ufo.position.x, ufo.position.y, 20, ufo.color, (80.0, 200.0))
                            trigger_shake(0.35, 8.0)
                            score += 200

                            if random.random() < 0.35:
                                try:
                                    kind = random.choice(["shield", "triple", "rapid"])
                                    Powerup(ufo.position.x, ufo.position.y, kind)
                                except Exception as e:
                                    print(f"Error spawning Powerup: {e}")

                            shot.kill()
                            ufo.kill()

            # Cek Tabrakan: Player vs Power-up
            for powerup in powerups:
                if player is not None and player.collides_with(powerup):
                    log_event("powerup_collected", kind=powerup.kind)
                    spawn_explosion_particles(powerup.position.x, powerup.position.y, 12, powerup.color, (60.0, 160.0))
                    trigger_shake(0.15, 3.0)

                    if powerup.kind == "shield":
                        player.shield_active = True
                    elif powerup.kind == "triple":
                        player.triple_shot_timer = 8.0
                    elif powerup.kind == "rapid":
                        player.rapid_fire_timer = 8.0

                    powerup.kill()

            # Cek Tabrakan: Asteroid vs Pemain
            if player is not None and player.invulnerability_timer <= 0:
                for asteroid in asteroids:
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
                                for ast in asteroids:
                                    if ast.position.distance_to(center) < 250:
                                        ast.kill()
                            else:
                                state = "GAME_OVER"
                                log_event("game_over", final_score=score)
                                if score > high_score:
                                    high_score = score
                                    save_high_score(high_score)
                                player.kill()

            # Cek Tabrakan: UFO vs Pemain
            if player is not None and player.invulnerability_timer <= 0:
                for ufo in ufos:
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
                                state = "GAME_OVER"
                                log_event("game_over", final_score=score)
                                if score > high_score:
                                    high_score = score
                                    save_high_score(high_score)
                                player.kill()

            # Cek Tabrakan: Tembakan UFO vs Pemain
            if player is not None and player.invulnerability_timer <= 0:
                for ufo_shot in ufo_shots:
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
                                state = "GAME_OVER"
                                log_event("game_over", final_score=score)
                                if score > high_score:
                                    high_score = score
                                    save_high_score(high_score)
                                player.kill()

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

            # Menggambar indikator durasi powerup
            hud_y = 60
            if player is not None:
                if player.triple_shot_timer > 0:
                    draw_text(game_surface, f"TRIPLE SHOT: {player.triple_shot_timer:.1f}s", 20, (255, 220, 0), SCREEN_WIDTH - 180, hud_y, align_center=False)
                    hud_y += 22
                if player.rapid_fire_timer > 0:
                    draw_text(game_surface, f"RAPID FIRE: {player.rapid_fire_timer:.1f}s", 20, (50, 255, 100), SCREEN_WIDTH - 180, hud_y, align_center=False)
                    hud_y += 22

            # Menggambar Teks Efek Level Up
            if level_up_timer > 0:
                pulse = math.sin(level_up_timer * 10) * 0.1 + 0.9
                text_size = int(48 * pulse)
                color = (255, 220, 0) if int(level_up_timer * 5) % 2 == 0 else (255, 255, 255)
                draw_text(game_surface, f"LEVEL UP: LEVEL {level}!", text_size, color, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 150)

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
            draw_text(game_surface, "B / LSHIFT : TRIGGER BOMB (PANIC BUTTON)", 22, COLOR_BOMB, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 205)
            draw_text(game_surface, "ESC : PAUSE GAME", 22, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 225)

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
            if score >= high_score and score > 0:
                draw_text(game_surface, "NEW HIGH SCORE!", 28, COLOR_PAUSE, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20)
            else:
                draw_text(game_surface, f"HIGH SCORE: {high_score}", 28, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20)
                
            draw_text(game_surface, "PRESS ENTER TO PLAY AGAIN", 32, COLOR_TEXT, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 90)
            draw_text(game_surface, "PRESS ESC TO RETURN TO MENU", 24, COLOR_TEXT_MUTED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 130)

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


