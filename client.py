import pygame
import socket
import sys
import math
import random

# --- Ініціалізація ---
pygame.init()
WIDTH, HEIGHT = 1000, 700
tile_size = 50
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Labyrinth Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22, bold=True)

# --- ЗАВАНТАЖЕННЯ ГРАФІКИ ---
def load_img(path, size, color):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size); surf.fill(color); return surf

wall_img = load_img("wall.png", (tile_size, tile_size), (50, 50, 55))
player_img = load_img("player.png", (35, 35), (0, 255, 0))
enemy_img = load_img("enemy.png", (35, 35), (255, 0, 0))
gun_img = load_img("gun.png", (35, 20), (255, 215, 0))

# --- ЛАБІРИНТ ---
def generate_level():
    walls = []
    empty_cells = []
    rows, cols = HEIGHT // tile_size, WIDTH // tile_size
    for r in range(rows):
        for c in range(cols):
            if r == 0 or r == rows-1 or c == 0 or c == cols-1 or (random.random() < 0.2 and (r,c) != (1,1)):
                walls.append(pygame.Rect(c * tile_size, r * tile_size, tile_size, tile_size))
            else:
                empty_cells.append((c * tile_size, r * tile_size))
    random.shuffle(empty_cells)
    guns = [pygame.Rect(empty_cells[0][0]+10, empty_cells[0][1]+15, 30, 20),
            pygame.Rect(empty_cells[1][0]+10, empty_cells[1][1]+15, 30, 20)]
    return walls, guns

walls, guns = generate_level()

# --- СТАТИСТИКА ---
player_rect = pygame.Rect(60, 60, 35, 35)
enemy_rect = pygame.Rect(-100, -100, 35, 35)
hp = 100
enemy_hp = 100
damage_to_send = 0
has_gun = False
bullets = []
game_over = False

# --- МЕРЕЖА ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(("localhost", 5555))
    client.setblocking(False)
except:
    print("Запустіть спочатку сервер!")

# --- ЛОГІКА ---
while True:
    screen.fill((30, 30, 35))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN and has_gun and not game_over:
            mx, my = pygame.mouse.get_pos()
            angle = math.atan2(my - player_rect.centery, mx - player_rect.centerx)
            bullets.append([player_rect.centerx, player_rect.centery, math.cos(angle), math.sin(angle)])

    if not game_over:
        keys = pygame.key.get_pressed()
        speed = 4
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * speed
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * speed
        
        # Рух з колізіями
        player_rect.x += dx
        for w in walls: 
            if player_rect.colliderect(w):
                if dx > 0: player_rect.right = w.left
                if dx < 0: player_rect.left = w.right
        player_rect.y += dy
        for w in walls:
            if player_rect.colliderect(w):
                if dy > 0: player_rect.bottom = w.top
                if dy < 0: player_rect.top = w.bottom

        # Підбір зброї
        for g in guns[:]:
            if player_rect.colliderect(g):
                has_gun = True
                guns.remove(g)

    # --- Мережевий обмін ---
    try:
        # Відправляємо: "x,y,hp,damage_i_did"
        client.send(f"{player_rect.x},{player_rect.y},{hp},{damage_to_send}".encode())
        damage_to_send = 0 # Скидаємо після відправки
        
        data = client.recv(128).decode()
        if data:
            ex, ey, ehp, dmg_taken = map(int, data.split(","))
            enemy_rect.x, enemy_rect.y, enemy_hp = ex, ey, ehp
            if dmg_taken > 0:
                hp -= dmg_taken # Отримуємо шкоду від ворога
    except: pass

    # --- Кулі та влучання ---
    for b in bullets[:]:
        b[0] += b[2] * 12
        b[1] += b[3] * 12
        b_rect = pygame.Rect(b[0]-3, b[1]-3, 6, 6)
        
        if b_rect.colliderect(enemy_rect):
            damage_to_send = 10 # Наступний пакет даних повідомить ворогу про шкоду
            bullets.remove(b)
            continue
            
        if any(b_rect.colliderect(w) for w in walls) or not screen.get_rect().collidepoint(b[0], b[1]):
            if b in bullets: bullets.remove(b)

    # --- МАЛЮВАННЯ ---
    for wall in walls: screen.blit(wall_img, (wall.x, wall.y))
    for g in guns: screen.blit(gun_img, (g.x, g.y))
    
    if hp > 0: screen.blit(player_img, player_rect)
    if enemy_hp > 0: screen.blit(enemy_img, enemy_rect)
    for b in bullets: pygame.draw.circle(screen, (255, 255, 0), (int(b[0]), int(b[1])), 4)

    # UI
    s1 = font.render(f"HP: {hp}", True, (0, 255, 0))
    s2 = font.render(f"ENEMY: {enemy_hp}", True, (255, 50, 50))
    screen.blit(s1, (20, 20))
    screen.blit(s2, (WIDTH-150, 20))

    if hp <= 0:
        game_over = True
        txt = font.render("GAME OVER! PRESS R TO RESTART", True, (255, 255, 255))
        screen.blit(txt, (WIDTH//2-150, HEIGHT//2))
        if pygame.key.get_pressed()[pygame.K_r]:
            hp = 100; game_over = False; player_rect.topleft = (60, 60)

    pygame.display.flip()
    clock.tick(60)