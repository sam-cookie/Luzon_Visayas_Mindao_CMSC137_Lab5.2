import socket
import threading
import sys

PUBLIC_KEY = 463    # e 
MODULUS_N  = 4331   # N  

def rsa_encrypt(message: str, e: int = PUBLIC_KEY, n: int = MODULUS_N) -> str:
    """Encrypt plaintext using the RSA public key.
    Returns space-separated cipher numbers."""
    return ' '.join(str(pow(ord(ch), e, n)) for ch in message)

def rsa_decrypt(cipher_text: str, d: int = None, n: int = MODULUS_N) -> str:
    """Decrypt a space-separated cipher string using the given private key."""
    if d is None:
        raise ValueError("Private key (d) is required for decryption.")
    numbers = cipher_text.strip().split(' ')
    return ''.join(chr(pow(int(num), d, n)) for num in numbers)

def masked_input(prompt: str) -> str:
    """
    Read user input one character at a time, printing '*' for each keystroke.
    Works on Windows (msvcrt) and Unix/macOS (termios).
    Falls back to regular input() if neither is available.
    """
    print(prompt, end='', flush=True)
    entered = []

    try:
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):       # enter key
                print()
                break
            elif ch == '\x08':           # backspace
                if entered:
                    entered.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == '\x03':           # ctrl c
                raise KeyboardInterrupt
            else:
                entered.append(ch)
                sys.stdout.write('*')
                sys.stdout.flush()
        return ''.join(entered)

    except ImportError:
        pass  

    try:
        import termios, tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n'):
                    print()
                    break
                elif ch in ('\x7f', '\x08'):  # delete
                    if entered:
                        entered.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ch == '\x03':
                    raise KeyboardInterrupt
                else:
                    entered.append(ch)
                    sys.stdout.write('*')
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ''.join(entered)

    except ImportError:
        pass  # fallback

    import getpass
    return getpass.getpass('')

print("=" * 50)
print("  RSA Encrypted Chat Client")
print("=" * 50)

nickname = input("Enter your nickname: ").strip()

print("\n[!] You appear to be in a public place.")
print("    Your private key input will be hidden with asterisks.\n")

while True:
    try:
        private_key_str = masked_input("Enter your private key (d): ")
        PRIVATE_KEY = int(private_key_str)
        break
    except ValueError:
        print("  [!] Invalid input. Please enter a numeric private key.")

print(f"\n[✓] Connected as '{nickname}' | RSA keys loaded (e={PUBLIC_KEY}, d=*****, N={MODULUS_N})\n")

HOST = '127.0.0.1'
PORT = 55555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def receive_messages():
    """Receive encrypted messages from the server and decrypt them."""
    while True:
        try:
            raw = client.recv(4096).decode('utf-8')
            if not raw:
                break

            # show raw encrypted form
            print(f"\n[ENCRYPTED received] {raw}")

            # decrypt using the user's private key
            try:
                plaintext = rsa_decrypt(raw, d=PRIVATE_KEY, n=MODULUS_N)
                print(f"[DECRYPTED]          {plaintext}\n> ", end='', flush=True)
            except Exception as ex:
                print(f"[!] Could not decrypt message. Wrong private key? ({ex})\n> ", end='', flush=True)

        except:
            print("\n[!] Connection lost. Disconnecting...")
            client.close()
            break

def write_messages():
    """Read user input, encrypt it, and send cipher text to the server."""
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            full_message = f"{nickname}: {user_input}"

            # encrypt before sending
            cipher_text = rsa_encrypt(full_message)
            print(f"[ENCRYPTED sent]     {cipher_text}")

            client.send(cipher_text.encode('utf-8'))

        except (EOFError, KeyboardInterrupt):
            print("\n[!] Exiting...")
            client.close()
            break
        except:
            client.close()
            break

# start
receive_thread = threading.Thread(target=receive_messages, daemon=True)
receive_thread.start()

write_thread = threading.Thread(target=write_messages)
write_thread.start()