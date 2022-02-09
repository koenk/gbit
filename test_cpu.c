/*
 * Placeholder interface implementation for the testing framework.
 *
 * The four functions starting with mycpu_ should be provided by your CPU to be
 * tested.
 *
 * Additionally, this file contains an example implementation of the mock MMU
 * that maps the tester's instruction memory area read-only, and tracks all
 * write operations.
 */

#include <string.h>

#include "lib/tester.h"

static size_t instruction_mem_size;
static uint8_t *instruction_mem;

static int num_mem_accesses;
static struct mem_access mem_accesses[16];

/*
 * Called once during startup. The area of memory pointed to by
 * tester_instruction_mem will contain instructions the tester will inject, and
 * should be mapped read-only at addresses [0,tester_instruction_mem_size).
 */
static void mycpu_init(size_t tester_instruction_mem_size,
                       uint8_t *tester_instruction_mem)
{
    instruction_mem_size = tester_instruction_mem_size;
    instruction_mem = tester_instruction_mem;

    /* ... Initialize your CPU here ... */
}

/*
 * Resets the CPU state (e.g., registers) to a given state state.
 */
static void mycpu_set_state(struct state *state)
{
    (void)state;

    num_mem_accesses = 0;

    /* ... Load your CPU with state as described (e.g., registers) ... */
}

/*
 * Query the current state of the CPU.
 */
static void mycpu_get_state(struct state *state)
{
    state->num_mem_accesses = num_mem_accesses;
    memcpy(state->mem_accesses, mem_accesses, sizeof(mem_accesses));

    /* ... Copy your current CPU state into the provided struct ... */
}

/*
 * Step a single instruction of the CPU. Returns the amount of cycles this took
 * (e.g., NOP should return 4).
 */
static int mycpu_step(void)
{
    int cycles = 0;

    /* ... Execute a single instruction in your CPU ... */

    return cycles;
}

struct tester_operations myops = {
    .init = mycpu_init,
    .set_state = mycpu_set_state,
    .get_state = mycpu_get_state,
    .step = mycpu_step,
};


/*
 * Example mock MMU implementation, mapping the tester's instruction memory
 * read-only at address 0, and logging all writes.
 */

uint8_t mymmu_read(uint16_t address)
{
    if (address < instruction_mem_size)
        return instruction_mem[address];
    else
        return 0xaa;
}

void mymmu_write(uint16_t address, uint8_t data)
{
    struct mem_access *access = &mem_accesses[num_mem_accesses++];
    access->type = MEM_ACCESS_WRITE;
    access->addr = address;
    access->val = data;
}
