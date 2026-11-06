import socket
import threading

PUBLIC_KEY  = 463 # e
PRIVATE_KEY = 127 # d
MODULUS_N   = 4331 # n

def rsa_encrypt(message: str) -> str:
    return ' '.join(str(pow(ord(ch), PUBLIC_KEY, MODULUS_N)) for ch in message)

def rsa_decrypt(cipher_text: str) -> str:
    numbers = cipher_text.strip().split(' ')
    return ''.join(chr(pow(int(n), PRIVATE_KEY, MODULUS_N)) for n in numbers)

HOST = '127.0.0.1'
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clients = []

def broadcast(raw_bytes: bytes, sender_client):
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

def handle_client(client):
    while True:
        try:
            raw = client.recv(4096)
            if not raw:
                break
            cipher_text = raw.decode('utf-8')
            try:
                plaintext = rsa_decrypt(cipher_text)
                print(f"[SERVER received – decrypted] {plaintext}")
            except Exception:
                print(f"[SERVER] Could not decrypt message: {cipher_text}")
            broadcast(raw, client)
        except:
            break
    remove_client(client)

def receive_connections():
    print(f"[SERVER] Running on {HOST}:{PORT} with RSA encryption (e={PUBLIC_KEY}, N={MODULUS_N})")
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