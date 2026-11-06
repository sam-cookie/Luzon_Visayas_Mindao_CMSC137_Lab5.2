import socket
import threading

HOST = '127.0.0.1'
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clients = []

def broadcast(raw_bytes: bytes, sender_client):
    # send the message to everyone except the person who sent it
    for client in clients:
        if client != sender_client:
            try:
                client.send(raw_bytes)
            except:
                remove_client(client)

def remove_client(client):
    if client in clients:
        clients.remove(client)
        client.close()
        print(f"[SERVER] A user disconnected.")

def handle_client(client):
    # just forward whatever comes in — server can't read it anyway
    while True:
        try:
            raw = client.recv(4096)
            if not raw:
                break

            print(f"[SERVER] Forwarding encrypted message (cannot decrypt)...")
            broadcast(raw, client)

        except:
            break

    remove_client(client)

def receive_connections():
    print(f"[SERVER] Running on {HOST}:{PORT}")
    print("[SERVER] Press Ctrl+C to stop.\n")
    server.settimeout(1.0)

    try:
        while True:
            try:
                client, address = server.accept()
                print(f"[SERVER] New connection from {address}")
                clients.append(client)
                thread = threading.Thread(target=handle_client, args=(client,), daemon=True)
                thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        for client in clients:
            client.close()
        server.close()
        print("[SERVER] Closed.")

if __name__ == "__main__":
    receive_connections()