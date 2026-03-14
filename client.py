import pygame
import socket
import sys
import math

pygame.init()

# Налаштування екрану
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Top-Down Shooter")
clock = pygame.time.Clock()

# --- ЗАВАНТАЖЕННЯ ГРАФІКИ ---
def load_img(path, color):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (50, 50))
    except:
        surf = pygame.Surface((50, 50))
        surf.fill(color)
        return surf

player_img = load_img("player.png", (0, 200, 0))
enemy_img = load_img("enemy.png", (200, 50, 50))

# --- СТІНИ ---
walls = [
    pygame.Rect(200, 200, 600, 30),
    pygame.Rect(150, 450, 200, 30),
    pygame.Rect(650, 450, 200, 30),
    pygame.Rect(485, 300, 30, 250)
]

# Об'єкти
player = pygame.Rect(500, 600, 45, 45)
enemy = pygame.Rect(0, 0, 45, 45)
speed = 5
bullets = [] # Список: [x, y, dx, dy]

# Мережа
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(("localhost", 5555))
    client.setblocking(False)
except:
    print("Не вдалося підключитися до сервера!")
    sys.exit()

def move_with_walls(rect, dx, dy, walls):
    # Рух по X
    rect.x += dx
    for wall in walls:
        if rect.colliderect(wall):
            if dx > 0: rect.right = wall.left
            if dx < 0: rect.left = wall.right
    # Рух по Y
    rect.y += dy
    for wall in walls:
        if rect.colliderect(wall):
            if dy > 0: rect.bottom = wall.top
            if dy < 0: rect.top = wall.bottom

while True:
    screen.fill((40, 40, 40))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Обчислення вектора напрямку
            dist_x = mx - player.centerx
            dist_y = my - player.centery
            angle = math.atan2(dist_y, dist_x)
            bullets.append([player.centerx, player.centery, math.cos(angle), math.sin(angle)])

    # 1. Рух гравця
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_d] - keys[pygame.K_a]) * speed
    dy = (keys[pygame.K_s] - keys[pygame.K_w]) * speed
    move_with_walls(player, dx, dy, walls)

    # 2. Мережа (синхронізація позицій)
    try:
        client.send(f"{player.x},{player.y}".encode())
        data = client.recv(64).decode()
        if data:
            ex, ey = map(int, data.split(","))
            enemy.x, enemy.y = ex, ey
    except: pass

    # 3. Малювання стін
    for wall in walls:
        pygame.draw.rect(screen, (80, 80, 80), wall)

    # 4. Малювання гравців (Картинки)
    screen.blit(player_img, (player.x, player.y))
    screen.blit(enemy_img, (enemy.x, enemy.y))

    # 5. Кулі
    for b in bullets[:]:
        b[0] += b[2] * 10 # рух x
        b[1] += b[3] * 10 # рух y
        b_rect = pygame.Rect(b[0]-3, b[1]-3, 6, 6)
        
        pygame.draw.circle(screen, (255, 255, 0), (int(b[0]), int(b[1])), 4)

        # Видалення куль (об стіни або межі)
        hit_wall = any(b_rect.colliderect(w) for w in walls)
        if hit_wall or not screen.get_rect().collidepoint(b[0], b[1]):
            bullets.remove(b)

    pygame.display.flip()
    clock.tick(60)
