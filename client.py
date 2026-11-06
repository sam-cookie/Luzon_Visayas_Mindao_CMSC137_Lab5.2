import socket
import threading
import sys
import json

MODULUS_N = 4331

def rsa_encrypt(message: str, e: int, n: int) -> str:
    return ' '.join(str(pow(ord(ch), e, n)) for ch in message)

def rsa_decrypt(cipher_text: str, d: int, n: int) -> str:
    numbers = cipher_text.strip().split(' ')
    return ''.join(chr(pow(int(num), d, n)) for num in numbers)

def masked_input(prompt: str) -> str:
    print(prompt, end='', flush=True)
    entered = []

    try:
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):
                print()
                break
            elif ch == '\x08':
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
                elif ch in ('\x7f', '\x08'):
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
        pass

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
        MY_PUBLIC_KEY = int(input("Enter your public key (e): ").strip())
        break
    except ValueError:
        print("  [!] Invalid input. Please enter a numeric public key.")

while True:
    try:
        PRIVATE_KEY = int(masked_input("Enter your private key (d): "))
        break
    except ValueError:
        print("  [!] Invalid input. Please enter a numeric private key.")

# Ask for the recipient's public key — this is what was missing before
# In a real system this would be exchanged out-of-band (e.g. shared beforehand)
RECIPIENT_N = 4331  # everyone shares the same modulus

print("\nEnter your recipient's public key details:")
RECIPIENT_E = int(input("  Recipient's e: ").strip())

print(f"\n[✓] Connected as '{nickname}' | RSA keys loaded (e={MY_PUBLIC_KEY}, d=*****, N={MODULUS_N})\n")

HOST = '127.0.0.1'
PORT = 55555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def receive_messages():
    while True:
        try:
            raw = client.recv(4096).decode('utf-8')
            if not raw:
                break

            print(f"\n[ENCRYPTED received] {raw}")

            # try decrypting with your private key and your own N
            # if it wasn't encrypted for you, it'll come out as gibberish
            try:
                plaintext = rsa_decrypt(raw, d=PRIVATE_KEY, n=MODULUS_N)
                print(f"[DECRYPTED]          {plaintext}\n> ", end='', flush=True)
            except Exception:
                print(f"[GIBBERISH]          (this message wasn't meant for you)\n> ", end='', flush=True)

        except:
            print("\n[!] Connection lost. Disconnecting...")
            client.close()
            break

def write_messages():
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            full_message = f"{nickname}: {user_input}"

            cipher_text = rsa_encrypt(full_message, e=RECIPIENT_E, n=RECIPIENT_N)

            print(f"[ENCRYPTED sent]     {cipher_text}")
            client.send(cipher_text.encode('utf-8'))

        except (EOFError, KeyboardInterrupt):
            print("\n[!] Exiting...")
            client.close()
            break
        except:
            client.close()
            break

receive_thread = threading.Thread(target=receive_messages, daemon=True)
receive_thread.start()

write_thread = threading.Thread(target=write_messages)
write_thread.start()