import pygame
import socket
import sys
import math
import random

# --- Ініціалізація ---
pygame.init()
W, H = 1000, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Labyrinth Shooter Online")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18, bold=True)

# --- Графіка ---
def load_img(name, size, color):
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        s = pygame.Surface(size); s.fill(color); return s

img_wall   = load_img("wall.png", (50, 50), (40, 40, 45))
img_player = load_img("player.png", (35, 35), (0, 255, 100))
img_enemy  = load_img("enemy.png", (35, 35), (255, 50, 50))
img_med    = load_img("medkit.png", (30, 30), (0, 200, 0))
img_boost  = load_img("boost.png", (30, 30), (200, 0, 200))

# --- Мережа ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(("localhost", 5555))
    maze_raw = client.recv(4096).decode()
    client.setblocking(False)
except: print("Запустіть сервер!"); sys.exit()

# --- Світ ---
walls = []
empty_cells = []
for i, char in enumerate(maze_raw):
    r, c = divmod(i, W // 50)
    rect = pygame.Rect(c*50, r*50, 50, 50)
    if char == "1": walls.append(rect)
    else: empty_cells.append((c*50+7, r*50+7))

# --- Змінні ---
player_rect = pygame.Rect(empty_cells[0][0], empty_cells[0][1], 35, 35)
enemy_rect = pygame.Rect(-100, -100, 35, 35)
hp, enemy_hp = 100, 100
bullets, pickups = [], []
damage_to_send, boost_timer, respawn_timer = 0, 0, 0

# --- Цикл ---
while True:
    dt = clock.tick(60)
    screen.fill((20, 20, 25))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and hp > 0:
            mx, my = pygame.mouse.get_pos()
            ang = math.atan2(my - player_rect.centery, mx - player_rect.centerx)
            bullets.append({"p": [player_rect.centerx, player_rect.centery], 
                            "v": [math.cos(ang)*12, math.sin(ang)*12], 
                            "d": 35 if boost_timer > 0 else 15})

    if hp > 0:
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * 4
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * 4
        
        player_rect.x += dx
        for w in walls:
            if player_rect.colliderect(w):
                if dx > 0: player_rect.right = w.left
                else: player_rect.left = w.right
        player_rect.y += dy
        for w in walls:
            if player_rect.colliderect(w):
                if dy > 0: player_rect.bottom = w.top
                else: player_rect.top = w.bottom
    else:
        respawn_timer -= dt
        if respawn_timer <= 0:
            player_rect.topleft = random.choice(empty_cells)
            hp = 100

    # Мережа
    try:
        client.send(f"{player_rect.x},{player_rect.y},{hp},{damage_to_send}".encode())
        damage_to_send = 0
        data = client.recv(2048).decode()
        if data:
            parts = data.split("|")
            e_info = parts[0].split(",")
            enemy_rect.x, enemy_rect.y, enemy_hp = int(e_info[0]), int(e_info[1]), int(e_info[2])
            if int(e_info[3]) > 0 and hp > 0: hp -= int(e_info[3])
            
            pickups = []
            for i, p_str in enumerate(parts[1:]):
                px, py, pt = p_str.split(":")
                pickups.append({"rect": pygame.Rect(int(px), int(py), 30, 30), "type": pt, "id": i})
    except: pass

    # Логіка
    if boost_timer > 0: boost_timer -= dt
    for p in pickups:
        if player_rect.colliderect(p["rect"]) and hp > 0:
            if p["type"] == "med": hp = min(100, hp + 30)
            else: boost_timer = 6000
            try: client.send(f"PICK:{p['id']}".encode())
            except: pass

    for b in bullets[:]:
        b["p"][0] += b["v"][0]; b["p"][1] += b["v"][1]
        br = pygame.Rect(b["p"][0]-3, b["p"][1]-3, 6, 6)
        if br.colliderect(enemy_rect) and enemy_hp > 0:
            damage_to_send = b["d"]; bullets.remove(b)
        elif any(br.colliderect(w) for w in walls): bullets.remove(b)

    # Малювання
    for w in walls: screen.blit(img_wall, w)
    for p in pickups: screen.blit(img_med if p["type"] == "med" else img_boost, p["rect"])
    if hp > 0: screen.blit(img_player, player_rect)
    if enemy_hp > 0: screen.blit(img_enemy, enemy_rect)
    for b in bullets: pygame.draw.circle(screen, (255, 255, 0), (int(b["p"][0]), int(b["p"][1])), 4)

    # UI
    screen.blit(font.render(f"HP: {max(0, hp)}", 1, (0, 255, 0)), (20, 20))
    screen.blit(font.render(f"ENEMY: {max(0, enemy_hp)}", 1, (255, 50, 50)), (W-140, 20))
    if hp <= 0:
        if respawn_timer <= 0: respawn_timer = 3000
        screen.blit(font.render(f"RESPAWN: {math.ceil(respawn_timer/1000)}s", 1, (255, 255, 255)), (W//2-60, H//2))
    
    pygame.display.flip()