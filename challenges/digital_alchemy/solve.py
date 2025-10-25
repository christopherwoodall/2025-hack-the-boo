import struct

def solve():
    expected_incantation = "USMWO[]\\iN[QWRYdqXle[i_bm^aoc"
    
    # From create_lead.py
    lead_header = b'MTRLLEAD'
    rng_init_bytes = b'\x97\x2c\xff\xbc'
    incantation_input = b'SPIRITUS_CODICIS_EXPERGISCERE'
    encrypted_payload = b'MPF~Sq={=tZ6k^_j:VE4k9RFv4b7a2hu'

    # Simulate athanor.c initialization
    rng_modulo = 0x26688d
    decryption_key = 0xdead # Initial key
    
    # Initialize rng_state from rng_init_bytes
    # (unsigned int)file_ptr[0xb] | (unsigned int)file_ptr[8] << 0x18 | (unsigned int)file_ptr[9] << 0x10 | (unsigned int)file_ptr[10] << 8;
    # This corresponds to little-endian interpretation of the 4 bytes
    rng_state = (rng_init_bytes[3] | \
                 (rng_init_bytes[0] << 24) | \
                 (rng_init_bytes[1] << 16) | \
                 (rng_init_bytes[2] << 8))

    base_offset = 0x40

    # From create_lead.py
    lead_header = b'MTRLLEAD'
    rng_init_bytes = b'\x97\x2c\xff\xbc'
    incantation_input = b'SPIRITUS_CODICIS_EXPERGISCERE'
    encrypted_payload = b'MPF~Sq={=tZ6k^_j:VE4k9RFv4b7a2hu'

    # Simulate athanor.c initialization (corrected based on decompile.txt)
    rng_modulo = 0x26688d
    decryption_key = 0x214f # Initial key from decompile.txt
    
    # Initialize rng_state from rng_init_bytes
    rng_state = (rng_init_bytes[3] | \
                 (rng_init_bytes[0] << 24) | \
                 (rng_init_bytes[1] << 16) | \
                 (rng_init_bytes[2] << 8))

    # Simulate Incantation check loop to update decryption_key (active in decompile.txt)
    for loop_counter in range(len(incantation_input)):
        file_ptr_char = incantation_input[loop_counter]
        decryption_key = (decryption_key + file_ptr_char) & 0xFFFFFFFF # Ensure decryption_key stays within unsigned 32-bit range

    # --- Decryption Phase ---
    decrypted_payload = bytearray(encrypted_payload)
    decrypted_payload_size = len(encrypted_payload)

    for decryption_loop_counter in range(decrypted_payload_size):
        rng_state = ((decryption_key & 0xFFFFFFFF) + (decryption_key & 0xFFFFFFFF) * (rng_state & 0xFFFFFFFF)) % rng_modulo
        keystream_byte = rng_state & 0xf # Corrected decryption: XOR with (rng_state & 0xf)
        
        # Decrypt using XOR
        decrypted_payload[decryption_loop_counter] = (decrypted_payload[decryption_loop_counter] ^ keystream_byte) & 0xFF # Ensure byte value

    print(f"Decrypted payload (hex): {decrypted_payload.hex()}")
    try:
        print(f"Decrypted payload (cp437): {decrypted_payload.decode('cp437')}")
    except UnicodeDecodeError:
        print("Could not decode with cp437")
    print(f"Decrypted payload (latin-1): {decrypted_payload.decode('latin-1')}")

if __name__ == "__main__":
    solve()
