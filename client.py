import pygame
import socket
import sys

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Network Shooter")
clock = pygame.time.Clock()

# Налаштування мережі
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(("localhost", 5555))
    client.setblocking(False) # ВАЖЛИВО: не дає грі зависнути
except Exception as e:
    print(f"Помилка підключення: {e}")
    sys.exit()

player = pygame.Rect(500, 350, 40, 40)
enemy = pygame.Rect(200, 200, 40, 40)
speed = 6
bullets = []

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Зберігаємо: [x, y, target_x, target_y]
            bullets.append([player.centerx, player.centery, mx, my])

    # Рух гравця
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: player.y -= speed
    if keys[pygame.K_s]: player.y += speed
    if keys[pygame.K_a]: player.x -= speed
    if keys[pygame.K_d]: player.x += speed

    # Мережевий обмін
    try:
        # Відправляємо свої координати
        client.send(f"{player.x},{player.y}".encode())
        
        # Пробуємо отримати координати ворога
        enemy_data = client.recv(64).decode()
        if enemy_data:
            ex, ey = enemy_data.split(",")
            enemy.x, enemy.y = int(ex), int(ey)
    except (BlockingIOError, Exception):
        pass # Якщо даних немає, просто йдемо далі

    # Малювання
    screen.fill((20, 20, 20))
    pygame.draw.rect(screen, (0, 200, 0), player) # Ви
    pygame.draw.rect(screen, (200, 50, 50), enemy) # Ворог

    # Логіка куль (тільки локально)
    for bullet in bullets[:]:
        dx = bullet[2] - bullet[0]
        dy = bullet[3] - bullet[1]
        dist = (dx**2 + dy**2) ** 0.5 # Виправлено піднесення до квадрата
        
        if dist > 0:
            bullet[0] += (dx / dist) * 10
            bullet[1] += (dy / dist) * 10
            pygame.draw.circle(screen, (255, 220, 0), (int(bullet[0]), int(bullet[1])), 5)
        
        if bullet[0] < 0 or bullet[0] > WIDTH or bullet[1] < 0 or bullet[1] > HEIGHT:
            bullets.remove(bullet)

    pygame.display.update()
    clock.tick(60)