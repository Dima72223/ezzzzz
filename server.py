import socket
import threading
import random
import time

# Налаштування
W, H = 1000, 700
TILE = 50
ROWS, COLS = H // TILE, W // TILE

def generate_maze():
    maze = ""
    for r in range(ROWS):
        for c in range(COLS):
            if r == 0 or r == ROWS-1 or c == 0 or c == COLS-1 or (random.random() < 0.18 and (r,c) != (1,1) and (r,c) != (ROWS-2, COLS-2)):
                maze += "1"
            else: maze += "0"
    return maze

MAZE_DATA = generate_maze()
player_data = [[60, 60, 100], [900, 600, 100]] # x, y, hp
damage_queue = [0, 0] # Шкода, яка чекає на гравця
pickups = []
lock = threading.Lock()

def spawner():
    global pickups
    while True:
        if len(pickups) < 5:
            rx, ry = random.randint(1, COLS-2)*TILE+10, random.randint(1, ROWS-2)*TILE+10
            with lock: pickups.append(f"{rx}:{ry}:{random.choice(['med', 'dmg'])}")
        time.sleep(10)

threading.Thread(target=spawner, daemon=True).start()

def handle_client(conn, p_id):
    global player_data, damage_queue, pickups
    other_id = 1 - p_id
    try:
        conn.send(MAZE_DATA.encode())
        while True:
            data = conn.recv(1024).decode()
            if not data: break
            if data.startswith("PICK:"):
                idx = int(data.split(":")[1])
                with lock: 
                    if idx < len(pickups): pickups.pop(idx)
                continue
            
            parts = data.split(",")
            if len(parts) >= 4:
                with lock:
                    player_data[p_id] = [int(parts[0]), int(parts[1]), int(parts[2])]
                    if int(parts[3]) > 0: damage_queue[other_id] += int(parts[3])
                    
                    enemy = player_data[other_id]
                    reply = f"{enemy[0]},{enemy[1]},{enemy[2]},{damage_queue[p_id]}"
                    if pickups: reply += "|" + "|".join(pickups)
                    conn.send(reply.encode())
                    damage_queue[p_id] = 0
    except: pass
    conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 5555))
s.listen(2)
print("Сервер готовий...")
pc = 0
while True:
    c, a = s.accept()
    threading.Thread(target=handle_client, args=(c, pc % 2)).start()
    pc += 1