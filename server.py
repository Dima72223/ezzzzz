import socket
import threading

# Налаштування
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Дозволяє перезапускати сервер миттєво
server.bind(("localhost", 5555))
server.listen(2)

print("Сервер запущений... Очікування гравців.")

# Початкові дані
positions = ["500,350", "200,200"]
lock = threading.Lock()

def handle(client, player_id):
    global positions
    print(f"Гравець {player_id} підключився.")
    
    while True:
        try:
            # Отримуємо координати "x,y"
            data = client.recv(64).decode()
            if not data:
                break

            with lock:
                # Оновлюємо позицію гравця
                positions[player_id] = data
                # Відправляємо позицію опонента
                other_id = 1 - player_id
                reply = positions[other_id]
            
            client.send(reply.encode())
        except:
            break

    print(f"Гравець {player_id} відключився.")
    client.close()

player_count = 0
while True:
    conn, addr = server.accept()
    if player_count < 2:
        thread = threading.Thread(target=handle, args=(conn, player_count))
        thread.start()
        player_count += 1
    else:
        conn.close() # Відхиляємо третього гравця