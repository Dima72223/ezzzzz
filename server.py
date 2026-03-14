import socket
import threading

# Налаштування
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 5555)) # 0.0.0.0 дозволяє підключення по мережі
server.listen(2)

print("Сервер запущено. Очікування гравців...")

# Позиції: "x,y" для кожного гравця
positions = ["500,600", "500,100"]
lock = threading.Lock()

def handle_client(conn, player_id):
    global positions
    print(f"Гравець {player_id} підключився.")
    while True:
        try:
            data = conn.recv(64).decode()
            if not data: break
            
            with lock:
                positions[player_id] = data
                other_id = 1 - player_id
                reply = positions[other_id]
            
            conn.send(reply.encode())
        except:
            break
    print(f"Гравець {player_id} відключився.")
    conn.close()

player_count = 0
while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, player_count % 2))
    thread.start()
    player_count += 1
