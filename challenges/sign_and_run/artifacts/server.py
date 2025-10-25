import subprocess
from zlib import crc32
from Crypto.Util.number import getPrime, inverse, bytes_to_long, long_to_bytes

p = getPrime(1024)
q = getPrime(1024)
N = p*q
e = 0x10001
phi = (p-1)*(q-1)
d = inverse(e, phi)
print(f"🔏 Iron Scribe awakened.\nPublic seal-parameters: N = {N}, e = {e}\n")

def display_menu():
    print("Choose your rite:")
    print("- inscribe [command]       (request a seal)")
    print("- invoke [command] [seal]  (execute with proof)")
    print("- depart")

def helper_sig(cmd):
  pt=bytes_to_long(cmd.encode())
  ct=pow(pt, d, N)
  return crc32(long_to_bytes(ct))

def sign_command(cmd):
  sig = helper_sig(cmd)
  print(f"Encrypted signature: {pow(sig, e, N)}")

def run_command(cmd, sig):
  if sig == helper_sig(cmd):
    print(f"⚙ Executing command under granted seal: {cmd}")
    result = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
    print("📜 Output:\n", result.stdout)
  else:
    print("⛔ The seal is false. The Iron Scribe rejects you.")
    exit()

while True:
    display_menu()
    user_input = input("> ").strip()

    if user_input.lower() == "depart":
        print("🌫 The Iron Scribe dims. Farewell, wanderer.")
        break

    elif user_input.lower().startswith("inscribe "):
        cmd = user_input[9:]
        sign_command(cmd)

    elif user_input.lower().startswith("invoke "):
        parts = user_input.split()
        if len(parts) < 3:
            print("⚠️ Format: invoke [command] [seal]")
            continue
        cmd = parts[1]
        seal = int(parts[2])
        run_command(cmd, seal)
    else:
        print("❓ The Scribe does not understand. Try again.")