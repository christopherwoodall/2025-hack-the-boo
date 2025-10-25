#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>
#include <gmp.h>
#include <zlib.h>
#include <stdlib.h>

#define NUM_THREADS 24
#define BABY_STEP_SIZE 65536  // 2^16

// Hash table for baby steps
typedef struct {
    mpz_t value;
    uint32_t signature;
    int valid;
} hash_entry_t;

typedef struct {
    mpz_t N;
    mpz_t encrypted_sig;
    uint32_t found_sig;
    int signature_found;
    pthread_mutex_t mutex;
} shared_data_t;

typedef struct {
    int thread_id;
    uint64_t start;
    uint64_t end;
    shared_data_t *shared;
    hash_entry_t *baby_steps;
} thread_arg_t;

uint32_t compute_crc32(const char *str) {
    return crc32(0L, (const Bytef *)str, strlen(str));
}

// Optimized modpow for e=65537
void fast_modpow_65537(mpz_t result, mpz_t base, mpz_t N) {
    mpz_t temp;
    mpz_init_set(temp, base);
    
    // Compute base^(2^16) = base^65536
    for (int i = 0; i < 16; i++) {
        mpz_mul(temp, temp, temp);
        mpz_mod(temp, temp, N);
    }
    
    // Now multiply by base once more: base^65536 * base = base^65537
    mpz_mul(result, temp, base);
    mpz_mod(result, result, N);
    
    mpz_clear(temp);
}

// Baby-step Giant-step attack
void *baby_step_giant_step_thread(void *arg) {
    thread_arg_t *targ = (thread_arg_t *)arg;
    mpz_t candidate, result, giant_step, temp, inverse_val;
    
    mpz_init(candidate);
    mpz_init(result);
    mpz_init(giant_step);
    mpz_init(temp);
    mpz_init(inverse_val);
    
    printf("Thread %d: Computing giant steps in range [%lu, %lu)\n", 
           targ->thread_id, targ->start, targ->end);
    
    // Compute (first_baby_step^65537)^(-1) mod N for giant steps
    mpz_set_ui(temp, 1);
    fast_modpow_65537(giant_step, temp, targ->shared->N);
    
    for (uint64_t i = targ->start; i < targ->end; i++) {
        pthread_mutex_lock(&targ->shared->mutex);
        if (targ->shared->signature_found) {
            pthread_mutex_unlock(&targ->shared->mutex);
            break;
        }
        pthread_mutex_unlock(&targ->shared->mutex);
        
        if (i % 1000000 == 0 && targ->thread_id == 0) {
            printf("Progress: %lu / %lu\n", i - targ->start, targ->end - targ->start);
        }
        
        mpz_set_ui(candidate, i);
        fast_modpow_65537(result, candidate, targ->shared->N);
        
        if (mpz_cmp(result, targ->shared->encrypted_sig) == 0) {
            pthread_mutex_lock(&targ->shared->mutex);
            if (!targ->shared->signature_found) {
                printf("\n✓ Thread %d found signature: %u\n", targ->thread_id, (uint32_t)i);
                targ->shared->found_sig = (uint32_t)i;
                targ->shared->signature_found = 1;
            }
            pthread_mutex_unlock(&targ->shared->mutex);
            break;
        }
    }
    
    mpz_clear(candidate);
    mpz_clear(result);
    mpz_clear(giant_step);
    mpz_clear(temp);
    mpz_clear(inverse_val);
    
    return NULL;
}

// Even better: Since sig is 32-bit, try a birthday attack approach
void crack_signature_optimized(mpz_t N, mpz_t encrypted_sig) {
    pthread_t threads[NUM_THREADS];
    thread_arg_t thread_args[NUM_THREADS];
    shared_data_t shared;
    
    mpz_init_set(shared.N, N);
    mpz_init_set(shared.encrypted_sig, encrypted_sig);
    shared.found_sig = 0;
    shared.signature_found = 0;
    pthread_mutex_init(&shared.mutex, NULL);
    
    printf("=== Optimized search using e=65537 property ===\n");
    printf("Using %d threads with fast modpow\n\n", NUM_THREADS);
    
    uint64_t range_size = (1ULL << 32) / NUM_THREADS;
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_args[i].thread_id = i;
        thread_args[i].start = i * range_size;
        thread_args[i].end = (i == NUM_THREADS - 1) ? (1ULL << 32) : (i + 1) * range_size;
        thread_args[i].shared = &shared;
        thread_args[i].baby_steps = NULL;
        
        pthread_create(&threads[i], NULL, baby_step_giant_step_thread, &thread_args[i]);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    if (shared.signature_found) {
        printf("\n=== Signature found: %u ===\n", shared.found_sig);
        printf("Now searching for collision...\n\n");
        
        // Collision search (same as before but simplified)
        const char *target = "cat<flag.txt";
        char test_cmd[256];
        int found = 0;
        
        #pragma omp parallel for
        for (uint64_t i = 0; i < (1ULL << 32); i++) {
            if (found) continue;
            
            snprintf(test_cmd, sizeof(test_cmd), "%s;echo %lu", target, i);
            uint32_t test_crc = compute_crc32(test_cmd);
            
            if (test_crc == shared.found_sig) {
                #pragma omp critical
                {
                    if (!found) {
                        printf("✓ Collision found!\n");
                        printf("Command: %s\n", test_cmd);
                        printf("invoke %s %u\n", test_cmd, shared.found_sig);
                        found = 1;
                    }
                }
            }
        }
    }
    
    mpz_clear(shared.N);
    mpz_clear(shared.encrypted_sig);
    pthread_mutex_destroy(&shared.mutex);
}

int main() {
    mpz_t N, encrypted_sig;
    mpz_init(N);
    mpz_init(encrypted_sig);
    
    mpz_set_str(N, 
        "21750027472302192941554544721260332670808113722932330991817696387609673227145555358778966513679468548649445155843523894418886922997827721854290524891543344113466578703146163942005614422316751363210572164382769850226770719245255674824310069266434534196656433824195213440792653096453124687664334022485851762535863381518775666298456328268435173113690972285943070089108489363565226043399516252005425765120040937031787174079664023909347859978301286705490325956548264631202067521267948703827213970607251248144410452951328171064427096251717734830021647862823206950023488237488426737437531863755149907305527530898105154580793", 
        10);
    
    mpz_set_str(encrypted_sig,
        "17171981356790730941012722500548300238917174179610631032629079246717153747901407445096723852083179949407847563472293979387111090367214995364490062240731245976461314901445575362394024611893174669649760343368216850624578850255474369469373557272649675555952092623619657218895500765807256314792389386679929937215574007109600139481224516223740868281715727336932529776742989807395815967965903027551787170036909815242764796492942885748382286349292931934085539421926587084339083425212949561848933274196457184801885995555519045948485975923465377802107292353109839302196799569721611145685366128574241231861804145615836283417535",
        10);
    
    crack_signature_optimized(N, encrypted_sig);
    
    mpz_clear(N);
    mpz_clear(encrypted_sig);
    
    return 0;
}