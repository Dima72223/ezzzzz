import socket
import threading

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 5555))
server.listen(2)

print("Сервер запущено. Очікування гравців...")

# Формат: "x,y,hp,damage_taken"
positions = ["500,600,100,0", "500,100,100,0"]
lock = threading.Lock()

def handle_client(conn, player_id):
    global positions
    print(f"Гравець {player_id} підключився.")
    while True:
        try:
            data = conn.recv(128).decode()
            if not data: break
            
            with lock:
                positions[player_id] = data
                other_id = 1 - player_id
                reply = positions[other_id]
                # Очищаємо прапорець шкоди після того, як його прочитали
                # щоб не віднімати HP нескінченно
                p_data = data.split(",")
                if len(p_data) > 3 and int(p_data[3]) > 0:
                    positions[player_id] = f"{p_data[0]},{p_data[1]},{p_data[2]},0"
            
            conn.send(reply.encode())
        except:
            break
    conn.close()

player_count = 0
while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, player_count % 2))
    thread.start()
    player_count += 1