#ifndef TESTER_H
#define TESTER_H

#include "common.h"

/*
 * Runs the tester, which will run all enabled instruction from instructions.h
 * and compare the output to a reference CPU.
 */
int tester_run(bool opt_keep_going_on_mismatch,
               bool opt_enable_cb_instruction_testing,
               bool opt_print_tested_instruction,
               bool opt_print_verbose_inputs);

/*
 *
 * Interface the tested CPU should implement.
 *
 */

/*
 * Called once during startup. The area of memory pointed to by
 * tester_instruction_mem will contain instructions the tester will inject, and
 * should be mapped read-only at addresses [0,tester_instruction_mem_size).
 */
void tcpu_init(size_t tester_instruction_mem_size,
               uint8_t *tester_instruction_mem);

/*
 * Resets the CPU state (e.g., registers) to a given state state.
 */
void tcpu_reset(struct state *state);

/*
 * Query the current state of the CPU.
 */
void tcpu_get_state(struct state *state);

/*
 * Step a single instruction of the CPU. Returns the amount of cycles this took
 * (e.g., NOP should return 4).
 */
int tcpu_step(void);


#endif
