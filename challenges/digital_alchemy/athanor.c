/*****************************************
 * gcc -o athanor athanor.c & ./athanor_rebuilt
 *****************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

int main(void)
{
    char temp_char;
    int comparison_result;
    long file_size_long;
    size_t incantation_length;
    char decoded_incantation[30];
    unsigned char xor_result;
    char offset_char;
    int payload_size;
    char *file_buffer;
    int incantation_expected_length;
    unsigned char base_offset;
    time_t start_time;
    unsigned int rng_modulo;
    char *file_ptr;
    int decrypted_payload_size;
    FILE *lead_file;
    char *expected_incantation;
    time_t current_time;
    unsigned int rng_state;
    int loop_counter;
    int decryption_loop_counter;
    int decryption_key;
    char *decrypted_payload;
    
    puts("Initializing the Athanor...");
    current_time = time((time_t *)0x0);
    expected_incantation = "USMWO[]\\iN[QWRYdqXle[i_bm^aoc";
    lead_file = fopen("lead.txt", "rb");
    
    if (lead_file == NULL) {
        perror("Error: Could not open lead.txt");
        return 1;
    }
   
    fseek(lead_file, 0, 2);
    file_size_long = ftell(lead_file);
    payload_size = (int)file_size_long;
    fseek(lead_file, 0, 0);
    file_buffer = (char *)malloc((long)payload_size);
    file_ptr = file_buffer;
    fread(file_buffer, 1, (long)payload_size, lead_file);
    fclose(lead_file);
    
    comparison_result = strncmp(file_ptr, "MTRLLEAD", 8);
    if (comparison_result == 0)
    {
        rng_modulo = 0x26688d;
        decryption_key = 0xdead; // Key from original solver
        rng_state = (unsigned int)file_ptr[0xb] |
                   (unsigned int)file_ptr[8] << 0x18 | 
                   (unsigned int)file_ptr[9] << 0x10 | 
                   (unsigned int)file_ptr[10] << 8;
       
        file_ptr = file_ptr + 8; // Move past MTRLLEAD
       
        // Anti-debug check (solver ignores it)
        file_ptr = file_ptr + 4; // Move past header
       
        base_offset = 0x40;
        decryption_key = 0xdead; // Key from original solver
       
        incantation_length = strlen(expected_incantation);
        incantation_expected_length = (int)incantation_length;
       
        // Incantation check
        for (loop_counter = 0; loop_counter < incantation_expected_length; loop_counter = loop_counter + 1)
        {
            offset_char = base_offset + (char)loop_counter;
            xor_result = base_offset ^ (offset_char + *file_ptr);
            temp_char = (char)((unsigned int)xor_result * 3 >> 8);
            decoded_incantation[loop_counter] =
                xor_result + ((unsigned char)(((unsigned char)(xor_result - temp_char) >> 1) + temp_char) >> 6) * -0x7f + '\x01';
            // decryption_key = decryption_key + *file_ptr; // This line is skipped in the solver
            file_ptr = file_ptr + 1;
        }
        // Anti-debug check (solver ignores it)
       
        decoded_incantation[loop_counter] = '\0';
        comparison_result = strcmp(decoded_incantation, expected_incantation); // Run the check
        if (comparison_result != 0)
        {
            printf("Incantation mismatch. The words fade into silence...");
            free(file_buffer);
            exit(1);
        }
        
        // --- Decryption Phase ---
        decrypted_payload = (char *)malloc(0x28); // 40 bytes, but we only use 32
       
        memcpy(decrypted_payload, file_ptr, 32); // Copy the 32-byte payload
        decrypted_payload_size = 32;              // Set loop counter to 32
       
        for (decryption_loop_counter = 0; decryption_loop_counter < decrypted_payload_size; decryption_loop_counter = decryption_loop_counter + 1)
        {
            rng_state = (decryption_key + decryption_key * rng_state) % rng_modulo;
           
            // Decrypt using SUBTRACTION
            decrypted_payload[decryption_loop_counter] = decrypted_payload[decryption_loop_counter] - (unsigned char)rng_state;
        }
        
        // Print the 32-byte flag to console
        printf("%s\n", decrypted_payload);
       
        free(file_buffer);
        free(decrypted_payload);
    }
    return 0;
}