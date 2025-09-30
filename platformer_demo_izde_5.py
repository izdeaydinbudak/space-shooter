import pygame
import sys
import random
import math
import time

pygame.init()

# Ekran ayarları
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
font = pygame.font.SysFont(None, 40)
clock = pygame.time.Clock()

# Müzik ve sesler
pygame.mixer.music.load("Toreador_song.mp3")
hit_sound = pygame.mixer.Sound("ouch.mp3")
pygame.mixer.music.set_volume(1)

# Renkler
WHITE = (255, 255, 255)
GREY = (180, 180, 180)
RED = (255, 0, 0)
BLUE = (0, 150, 255)
YELLOW = (255, 255, 0)

sound_on = True

def draw_text(text, x, y, selected=False):
    color = WHITE if selected else GREY
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(x, y))
    screen.blit(surface, rect)
    return rect

layers = [
    {"image": pygame.image.load("nebula_1.jpg").convert_alpha(), "y": 0, "speed": 0.001},
    {"image": pygame.image.load("stars_2.png").convert_alpha(), "y": 0, "speed": 0.2},
    {"image": pygame.image.load("purple_dust_3.png").convert_alpha(), "y": 0, "speed": 0.3},
]
laser_img_player = pygame.image.load("player_laser_gun.png").convert_alpha()
laser_img_player = pygame.transform.scale(laser_img_player, (32, 128))
laser_img_enemy = pygame.image.load("enemy_laser_gun.png").convert_alpha()
laser_img_enemy = pygame.transform.scale(laser_img_enemy, (32, 128))

for layer in layers:
    layer["image"] = pygame.transform.scale(layer["image"], (WIDTH, HEIGHT))

def draw_parallax():
    for layer in layers:
        img, y, speed = layer["image"], layer["y"], layer["speed"]
        y += speed
        if y >= HEIGHT:
            y = 0
        layer["y"] = y
        screen.blit(img, (0, y))
        screen.blit(img, (0, y - HEIGHT))

def leadership(nickname,score,remaining_seconds):
    import requests

    data = {"nickname": nickname, "score": score, "time": remaining_seconds}
    response = requests.post("http://127.0.0.1:5000/submit", json=data)

    print("Status code:", response.status_code)
    print("Response text:", response.text)

    try:
        print("JSON:", response.json())
    except Exception as e:
        print("JSON decode error:", e)

def menu():
    selected = 0
    options = ["Start Game", "Toggle Sound", "Quit"]
    input_box = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 - 150, 280, 50)
    color_inactive = (128, 128, 128)  # gri
    color_active = (30, 144, 255)     # dodgerblue2
    col = color_inactive
    active = False
    nickname = ""
    while True:
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
            # Tıklanan yer input_box içindeyse aktif yap, değilse pasif yap
                if input_box.collidepoint(event.pos):
                    active = True
                    col = color_active
                else:
                    active = False
                    col = color_inactive

            elif event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        print(f"Girilen isim: {nickname}")
                    elif event.key == pygame.K_BACKSPACE:
                        nickname = nickname[:-1]
                    else:
                        nickname += event.unicode
                else:            
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(options)
                    elif event.key == pygame.K_RETURN:
                        choice = options[selected]
                        if choice == "Start Game":
                            game(nickname)
                        elif choice == "Toggle Sound":
                            global sound_on
                            sound_on = not sound_on
                        elif choice == "Quit":
                            pygame.quit(); sys.exit()

        for i, option in enumerate(options):
            draw_text(option, WIDTH // 2, 250 + i * 60, selected == i)
        # Nickname kutusu
        pygame.draw.rect(screen, col, input_box, 2)
        text_surface = font.render(nickname or "Enter nickname...", True, (255, 255, 255))
        screen.blit(text_surface, (input_box.x + 5, input_box.y + 10))
        input_box.w = max(280, text_surface.get_width() + 10)
        pygame.display.flip()
        clock.tick(60)

# Sınıflar
class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - 25, HEIGHT - 80, 50, 50)
        self.speed = 5
        self.health = 3

    def move(self, keys):
        if keys[pygame.K_LEFT]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        if keys[pygame.K_UP]: self.rect.y -= self.speed
        if keys[pygame.K_DOWN]: self.rect.y += self.speed
        self.rect.clamp_ip(screen.get_rect())

    def draw(self):
        pygame.draw.rect(screen, BLUE, self.rect)


class Enemy:
    def __init__(self, speed):
        self.rect = pygame.Rect(random.randint(0, WIDTH - 40), -40, 40, 40)
        self.speed = speed
        self.shoot_delay = random.randint(1000, 3000)
        self.last_shot_time = pygame.time.get_ticks()
        self.hitbox = self.rect.copy()

    def move(self):
        self.rect.y += self.speed
        self.hitbox.y += self.speed

    def should_shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_delay:
            self.last_shot_time = now
            return True
        return False

    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)


class Bullet:
    def __init__(self, x, y):
        self.image = pygame.transform.scale(laser_img_player, (60, 120))
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 6, 25)
        self.hitbox.center = self.rect.center
        self.speed = -8

    def draw(self):
        screen.blit(self.image, self.rect.topleft)

    def move(self):
        self.rect.y += self.speed
        self.hitbox.y += self.speed


class EnemyBullet:
    def __init__(self, x, y, speed):
        self.image = pygame.transform.scale(laser_img_enemy, (60, 120))
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 6, 25)
        self.hitbox.center = self.rect.center
        self.speed = speed

    def draw(self):
        screen.blit(self.image, self.rect.topleft)

    def move(self):
        self.rect.y += self.speed
        self.hitbox.y += self.speed

class Boss:
    def __init__(self, x, y, speed):
        self.image = pygame.transform.scale(laser_img_enemy, (100, 200))
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect.copy()
        self.speed = speed
        self.last_player_x = None
        self.last_shot_time = 0
        self.shoot_cooldown = 800  # ms
        self.last_direction_change = pygame.time.get_ticks()
        self.direction = 1  # 1: sağa, -1: sola

    def draw(self):
        screen.blit(self.image, self.rect.topleft)

    def update_ai(self, player_x):
        now = pygame.time.get_ticks()

        # Zigzag hareket için sinus dalgası gibi dalgalanma
        zigzag_amplitude = 40  # Ne kadar geniş zigzag yapsın
        zigzag_frequency = 0.001  # Ne kadar hızlı zigzag yapsın
        offset = int(math.sin(now * zigzag_frequency) * zigzag_amplitude)

        # Player’a doğru yönel + zigzag ekle
        if abs(self.rect.centerx - player_x) > 10:
            direction = 1 if player_x > self.rect.centerx else -1
            self.rect.x += direction * self.speed

        # Zigzag eklendi
        self.rect.x += offset // 10

        self.hitbox.center = self.rect.center

        # Ateş etme kararı (player’a hizalanınca)
        if abs(self.rect.centerx - player_x) < 60:
            if now - self.last_shot_time > self.shoot_cooldown:
                self.last_shot_time = now
                # Ateş ettikten sonra bir yöne kaç
                self.rect.x += random.choice([-80, 80])
                return True

        return False

# Oyun fonksiyonu
def game(nickname):
    start_time = pygame.time.get_ticks()  # Başlangıç zamanı (milisaniye cinsinden)
    time_limit = 1 * 60 * 1000  # 5 dakika = 300000 ms

    player = Player()
    bullets = []
    enemies = []
    enemy_bullets = []
    boss = None
    boss_health = 30
    boss_spawned = False

    enemy_speed = 2
    enemy_bullet_speed = 5
    score = 0
    shoot_cooldown = 300
    last_shot = pygame.time.get_ticks()
    level, max_level, last_score = 1, 2, 0
    spawn_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(spawn_timer, 1000)

    running = True
    while running:
        # Zaman kontrolü
        elapsed_time = pygame.time.get_ticks() - start_time
        remaining_seconds = max(0, (time_limit - elapsed_time) // 1000)

        # Zaman dolduysa oyun biter
        if elapsed_time >= time_limit:
            draw_text("TIME IS UP! GAME OVER", WIDTH // 2, HEIGHT // 2, selected=True)
            pygame.display.flip()
            pygame.time.wait(3000)
            leadership(nickname,remaining_seconds,score)
            return


        draw_parallax()
        keys = pygame.key.get_pressed()
        player.move(keys)

        now = pygame.time.get_ticks()
        if keys[pygame.K_SPACE] and now - last_shot > shoot_cooldown:
            bullets.append(Bullet(player.rect.centerx, player.rect.top))
            last_shot = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == spawn_timer:
                if level < max_level:
                    enemies.append(Enemy(enemy_speed))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        # Mermileri hareket ettir
        for bullet in bullets[:]:
            bullet.move()
            if bullet.rect.bottom < 0:
                bullets.remove(bullet)

        # Düşmanları güncelle
        for enemy in enemies[:]:
            enemy.move()
            if enemy.rect.top > HEIGHT:
                enemies.remove(enemy)

            for bullet in bullets[:]:
                if enemy.hitbox.colliderect(bullet.hitbox):
                    bullets.remove(bullet)
                    enemies.remove(enemy)
                    score += 1
                    break

            if enemy.rect.colliderect(player.rect):
                enemies.remove(enemy)
                player.health -= 1

            if enemy.should_shoot():
                enemy_bullets.append(EnemyBullet(enemy.rect.centerx, enemy.rect.bottom, enemy_bullet_speed))

        # Boss seviyesine geçiş
        if score - last_score >= 5 and level < max_level:
            level += 1
            last_score = score
            enemy_speed += 1
            enemy_bullet_speed += 1

        # Boss spawn ve davranış
        if level == max_level and not boss_spawned:
            boss = Boss(WIDTH // 2, 80, 2)
            boss_spawned = True

        if boss:
            if boss.update_ai(player.rect.centerx):
                enemy_bullets.append(EnemyBullet(boss.rect.centerx, boss.rect.bottom, enemy_bullet_speed))

            boss.draw()
            screen.blit(font.render(f"Boss Health: {boss_health}", True, RED), (400, 50))

            for bullet in bullets[:]:
                if boss.hitbox.colliderect(bullet.hitbox):
                    bullets.remove(bullet)
                    boss_health -= 1
                    score += 1

            if boss_health <= 0:
                win_text = font.render("YOU WIN!", True, (0, 255, 0))
                screen.blit(win_text, (WIDTH // 2 - 80, HEIGHT // 2))
                pygame.display.flip()
                pygame.time.wait(3000)
                leadership(nickname,score,remaining_seconds)
                return

        # Düşman mermileri
        for eb in enemy_bullets[:]:
            eb.move()
            if eb.rect.top > HEIGHT:
                enemy_bullets.remove(eb)
            elif eb.hitbox.colliderect(player.rect):
                enemy_bullets.remove(eb)
                player.health -= 1
                if sound_on:
                    hit_sound.play()
                if player.health <= 0:
                    draw_text("GAME OVER", WIDTH // 2, HEIGHT // 2, selected=True)
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    leadership(nickname,remaining_seconds,score)
                    return

        player.draw()
        for bullet in bullets: bullet.draw()
        for enemy in enemies: enemy.draw()
        for eb in enemy_bullets: eb.draw()

        screen.blit(font.render(f"Score: {score}  Level: {level}", True, WHITE), (10, 10))
        screen.blit(font.render(f"{nickname} + Health: {player.health}", True, RED), (10, 50))
        screen.blit(font.render(f"Remaining time: {remaining_seconds}", True, RED), (10, 200))
        
        pygame.display.flip()
        clock.tick(60)
    
    
menu()
