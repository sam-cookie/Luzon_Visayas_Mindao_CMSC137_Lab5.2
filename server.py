import socket
import threading

PUBLIC_KEY  = 463   # e
PRIVATE_KEY = 127   # d
MODULUS_N   = 4331  # N

def rsa_encrypt(message: str) -> str:
    """Encrypt a plaintext string using the RSA public key.
    Each character is encrypted as: (ascii^e) mod N
    Returns a space-separated string of cipher numbers."""
    return ' '.join(str(pow(ord(ch), PUBLIC_KEY, MODULUS_N)) for ch in message)

def rsa_decrypt(cipher_text: str) -> str:
    """Decrypt a space-separated cipher string using the RSA private key.
    Each number is decrypted as: (cipher^d) mod N → ASCII char"""
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
    """Forward the raw cipher bytes to all clients except the sender."""
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
    """
    Receives encrypted messages from a client, decrypts them (so the server
    can read/log them), then re-broadcasts the SAME cipher text to others.
    """
    while True:
        try:
            raw = client.recv(4096)
            if not raw:
                break

            cipher_text = raw.decode('utf-8')

            # decrypt on the server side so the server owner can see plaintext
            try:
                plaintext = rsa_decrypt(cipher_text)
                print(f"[SERVER received – decrypted] {plaintext}")
            except Exception:
                print(f"[SERVER] Could not decrypt message: {cipher_text}")

            # forward the cipher text as-is to other clients
            broadcast(raw, client)

        except:
            break

    remove_client(client)

def receive_connections():
    print(f"[SERVER] Running on {HOST}:{PORT} with RSA encryption (e={PUBLIC_KEY}, N={MODULUS_N})")
    while True:
        client, address = server.accept()
        print(f"[SERVER] New connection from {address}")
        clients.append(client)

        thread = threading.Thread(target=handle_client, args=(client,), daemon=True)
        thread.start()

if __name__ == "__main__":
    receive_connections()