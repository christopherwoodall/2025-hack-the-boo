#!/usr/bin/env python3

import struct
import sys

def solve_payload(encrypted_payload, initial_rng_state, decryption_key):
    """
    Decrypts the 32-byte payload.
    This version tries an ADD cipher instead of SUB.
    """
    rng_modulo = 0x26688d
    decrypted_flag_bytes = []
    
    # We must operate on 32-bit unsigned integers
    rng_state = initial_rng_state & 0xFFFFFFFF
    key = decryption_key & 0xFFFFFFFF
    
    print(f"[+] Decrypting payload with 32-bit math, key: {hex(key)} ...")
    
    for i in range(32):
        # 1. Emulate C's 32-bit unsigned arithmetic
        term2 = (key * rng_state) & 0xFFFFFFFF
        sum_val = (key + term2) & 0xFFFFFFFF
        rng_state = sum_val % rng_modulo

        # 2. Get the decryption byte
        rng_byte = rng_state & 0xFF 
        
        # 3. --- THIS IS THE FINAL CHANGE ---
        # Try ADDITION instead of subtraction
        encrypted_byte = encrypted_payload[i]
        decrypted_byte = (encrypted_byte + rng_byte) & 0xFF
        # --- END CHANGE ---
        
        decrypted_flag_bytes.append(decrypted_byte)

    try:
        final_flag = "".join(chr(b) for b in decrypted_flag_bytes)
        return final_flag
    except UnicodeDecodeError:
        print("[!] Decryption failed. Final bytes are not valid ASCII.", file=sys.stderr)
        return None

def main():
    filename = "lead.txt"
    try:
        with open(filename, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"[!] Error: '{filename}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Read {len(data)} bytes from '{filename}'.")

    if len(data) < 72: # 8 + 4 + 28 + 32 = 72
        print("[!] Error: File is too small. Expected at least 72 bytes.", file=sys.stderr)
        sys.exit(1)
    if data[0:8] != b'MTRLLEAD':
        print("[!] Error: Invalid file header.", file=sys.stderr)
        sys.exit(1)

    # 1. Use the "FIXED" PARSING
    # (Assumes 'file_ptr = file_ptr + 4;' should be active)
    rng_state = data[11] | (data[8] << 24) | (data[9] << 16) | (data[10] << 8)
    incantation_from_file = data[12:40] # Bytes 12 through 39
    payload_from_file = data[40:72]   # Bytes 40 through 71

    print(f"[+] Parsed RNG seed: {hex(rng_state)}")
    print(f"[+] Parsed INCANTATION (raw, fixed): {incantation_from_file!r}")
    print(f"[+] Parsed PAYLOAD (raw, fixed): {payload_from_file!r}")

    if len(payload_from_file) != 32:
        print(f"[!] Error: Payload is {len(payload_from_file)} bytes, expected 32.", file=sys.stderr)
        sys.exit(1) 

    # 2. Use the "STATIC" KEY
    # (Assumes 'decryption_key = ...' was correctly commented out)
    final_decryption_key = 0xdead
    
    print(f"[+] Using static key: {hex(final_decryption_key)}")
    
    # 3. Decrypt the payload
    final_flag = solve_payload(payload_from_file, rng_state, final_decryption_key)
    
    if final_flag:
        print("\n" + "="*40)
        print(f"  FINAL FLAG:\n  {final_flag}")
        print("="*40)

if __name__ == "__main__":
    main()