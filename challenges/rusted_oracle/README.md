# Rusted Oracle

This is a reverse engineering challenge. The goal is to restore the decrepit mechanism.

## Initial Triage

- The challenge directory contains an executable file named `rusted_oracle` and a directory named `artifacts`.
- The `file` command shows that `rusted_oracle` is a 64-bit ELF executable and is not stripped.

## Static Analysis

- The `strings` command revealed several interesting strings, including:
    - `On a rusted plate, faint letters reveal themselves: %s`
    - `A forgotten machine still ticks beneath the stones.`
    - `Its gears grind against centuries of rust.`
    - `[ a stranger approaches, and the machine asks for their name ]`
    - `Corwin Vell`
    - `[ the gears begin to turn... slowly... ]`
    - `[ the machine falls silent ]`
    - `machine_decoding_sequence`
- The `objdump` output shows that the `machine_decoding_sequence` function performs a series of bitwise operations on data located at the `enc` address.
- The `objdump` output of the `.data` section shows the encrypted data at address `0x4050`.

## Solution

The final solution was to create a python script that replicates the decoding algorithm and prints the flag. The decoding algorithm is as follows:

1. XOR with `0x524E`
2. Rotate right by 1 bit
3. XOR with `0x5648`
4. Rotate left by 7 bits
5. Shift right by 8 bits
6. Extract the lowest byte

The encrypted flag is stored at address `0x4050` in the binary's data section.

```python
enc = [
  0xfffe, 0xff8e, 0xffd6, 0xff32, 0xff12, 0xff72,
  0xfe1a, 0xff1e, 0xff9e, 0xfe1a, 0xff66, 0xffc2,
  0xfe6a, 0xffd2, 0xfe0e, 0xff6e, 0xff6e, 0xfe4e,
  0xfe5a, 0xfe5a, 0xfe1a, 0xfe5a, 0xff2a
]

flag = ''
for i in range(len(enc)):
    val = enc[i]
    
    # XOR by 0x524e
    val ^= 0x524e
    
    # ROR by 1
    val = (val >> 1) | ((val & 1) << 15)

    # XOR by 0x5648
    val ^= 0x5648

    # ROL by 7
    val = ((val << 7) | (val >> (16 - 7))) & 0xFFFF

    # SHR by 8
    val >>= 8
    
    flag += chr(val & 0xff)

print(flag)
```

## Flag

`HTB{sk1pP1nG-C4ll$!!1!}`
