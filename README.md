# GBIT - Game Boy Instruction Tester

Differential testing framework for Game Boy CPUs.

Tests all instructions of a Game Boy CPU against a known-good implementation to
detect implementation bugs. Useful for testing and debugging, especially early
on in Game Boy emulator development where test ROMs do not run yet. Compatible
with Game Boy emulators written in C, C++ and Python.

For each instruction in the Game Boy instruction set, the framework will issue
many different executions with varying input states, each time comparing the
output state to a known-good state. This allows for easy detection of
implementation errors, such as calculating the wrong results, setting flags
incorrectly, jumping to the wrong place and even accidentally corrupting other
state.

To test your CPU implementation, it has to implement four functions and track
all memory accesses made by the test CPU (see below for more details). This
minimal interface should allow any emulator written in C and C++ to be easily
tested. Additionally, a Python wrapper is available.

The known-good CPU implementation included in the framework is based on
[my own Game Boy emulator](https://github.com/koenk/gbc), which has been
verified with
[test ROMs](https://gekkio.fi/blog/2016/game-boy-test-rom-dos-and-donts/) such
as the [Blargg](https://gbdev.gg8.se/files/roms/blargg-gb-tests/) ones. However,
the framework can compare any two Game Boy CPUs, and the interface for the
reference CPU is similar to the one used for the public test CPU one, so
swapping out the reference implementation is trivial.

The framework contains a list of instructions, how to encode/assemble all
variants and operands, and which state of the CPU is relevant to that
instruction. This information is used to generate a minimal (but still complete)
test set per instruction, resulting in much faster execution of tests than brute
forcing all inputs. Because this framework runs standalone it is also generally
much faster than a test ROM, because other parts of the system to not need to be
emulated.

This framework was original developed for the
[gb-fpga](https://github.com/koenk/gb-fpga) project, where a Verilog CPU
implementation (running in a simulator) is compared against an emulated CPU.


# How to use

## Hooking up your CPU implementation

The interface for the test framework is defined in `lib/tester.h`, which you
should include in your code. The test framework requires four callback functions
into your CPU, as defined in the `tester_operations` struct. These functions
should behave as follows:

```c
    void init(size_t instruction_mem_size, uint8_t *instruction_mem);
```

Called once at startup. Here you should perform any initialization needed by
your CPU. Additionally, the arguments passed in by the tester specify a memory
area of `instruction_mem_size` bytes, which should be mapped read-only at
address 0 for your CPU (see below).

```c
    void set_state(struct state *state);
```

Reset your CPU to a specific state, as defined in the `state` struct (format can
be found below). This function is called in between each different instruction
and set of inputs per instruction.

```c
    void get_state(struct state *state);
```

Load the current state of your CPU into the `state` struct (as defined below).
This function is called after each test run for different instruction and input
combinations.

```c
    int step(void);
```

Step a single instruction of your CPU, and return the number of cycles spent
doing so. This means machine cycles (running at a 4.19 MHz clock), so for
instance the `NOP` instruction should return 4.

The file `test_cpu.c` contains some example and boilerplate code to help you get
started with implementing these functions.


### Memory accesses

Instructions are fetched from memory by your CPU. Additionally, many instruction
will read from or write to memory. Because of this, your implementation should
also provide a mock MMU.

For reads, addresses 0 through `instruction_mem_size` (as passed in by the
`init` callback) should return the bytes pointed to by `instruction_mem`. These
bytes will be the instruction that `step` will execute.  Note that the memory
area pointed to by `instruction_mem` will be modified by the test framework in
between each instruction that is executed. Your `init` implementation should
therefore not copy out the bytes, but instead save the pointer to this area so
it can be read on-demand. All other memory reads (outside of this particular
area) should return the value `0xAA`.

For writes, your mock MMU does not need to emulate memory. Instead it should
keep a log of all memory accesses so this behavior can be compared against the
known-good implementation inside the test framework. Each 8-bit memory access
should be logged as a `struct mem_access` entry (defined below). Each entry has
a type (which is always `MEM_ACCESS_WRITE`), the address being written to, and
the value that is being written. For instructions that write 16-bit values, two
log entries should be created for each byte. The order of these memory access in
the log does not matter; the test framework will reorder these internally.

The file `test_cpu.c` contains an example implementation of an MMU, that should
be sufficient for most users.


### Data types

The above callback functions are passed into the framework via the following
struct:

```c
    struct tester_operations {
        void (*init)(size_t instruction_mem_size, uint8_t *instruction_mem);
        void (*set_state)(struct state *state);
        void (*get_state)(struct state *state);
        int (*step)(void);
    };
```

All data types related to the state struct, as used by `set_state` and
`get_state`, are defined as follows:

```c
    #define MEM_ACCESS_WRITE 1

    struct mem_access {
        int type;
        u16 addr;
        u8 val;
    };

    struct state {
        union {
            struct {
                u16 AF, BC, DE, HL;
            } reg16;
            struct {
                u8 F, A, C, B, E, D, L, H;
            } reg8;
        };
        u16 SP;
        u16 PC;
        bool halted;
        bool interrupts_master_enabled;

        int num_mem_accesses;
        struct mem_access mem_accesses[16];
    };
```

Registers are placed in a union so they can be accessed in both 8-bit and 16-bit
form. To access one of these, use the following syntax: `state->reg8.A` and
`state->reg16.BC`.
The `halted` flag should reflect whether your CPU has halted because of the
executed instruction (e.g., `HALT`).
The `interrupts_master_enabled` is used for setting and retrieving the IME flag
of your CPU (set/reset by `EI`, `DI` and `RETI`).
All memory accesses that are writes should be recorded in the `mem_accesses`
array.


### C++ compatibility

The test framework is written in C, but can interact with CPUs written in C++ as
well by simply including the same header file (`lib/tester.h`). When using the
provided `main.c`, make sure your CPU operations struct is visible to C code
(i.e., define it inside an `extern "C"` block). The build infrastructure
(described below) can already handle .cpp files.


### Python wrapper

A wrapper is available for testing Game Boy emulators written in Python. This
wrapper uses the same framework library, and thus has similar usage and data
types. For more details about this wrapper and how to use it, see the python
directory.


## Building and running

The provided Makefile will compile the test framework (in the `lib` directory)
as a shared object file (`libgbit.so`). Additionally, it will build `main.c` to
parse command-line arguments and start the tests. You can add your own .c and
.cpp files to the `BINSRC` in `Makefile`, which will be linked into the `gbit`
binary.

To compile and run the tests, simply run make and the resulting binary:

    $ make
    $ ./gbit

This will test each instruction with different input states (e.g., different
values set to each register, different arguments) and compare the output to
a reference (known-good) CPU. If a mismatch is detected, the input state and the
two outputs states (including memory accesses) are logged:

      === STATE MISMATCH ===

     - Instruction -
    LDD (HL), A

     - Input state -
     PC   SP   AF   BC   DE   HL  ZNHC hlt IME
    0000 0000 0000 0000 0000 0000 0000  0   0


     - Test-CPU output state -
     PC   SP   AF   BC   DE   HL  ZNHC hlt IME
    0001 0000 0000 0000 0000 0000 0000  0   0
    Mem write: addr=0000 val=00


     - Correct output state -
     PC   SP   AF   BC   DE   HL  ZNHC hlt IME
    0001 0000 0000 0000 0000 ffff 0000  0   0
    Mem write: addr=0000 val=00

Here we see the `LDD (HL), A` instruction produced an incorrect state after
execution. We can see the `HL` register is not `0xffff` as it is supposed to be.
All other state does match up, and the memory write logs are identical too.

Normally, the tester will stop execution on the first error it encounters. By
running `./gbit -k` it will instead skip to the next opcode or instruction, and
print a summary of all non-functional opcodes at the end:

    Tested 67/67 instructions, 65 passed and 2 failed
    Successfully tested 242/244 opcodes

    Table of untested/incorrect opcodes:
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- 32 -- 34 -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

This table matches the layout of instruction tables such as [this
one](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html).

Note the definition of *instruction* in the test framework. Here we see there
are 244 valid (non-CB-prefixed) opcodes but only 67 valid instructions. In this
framework, an instruction refers to a class of instructions, such as `ADD r8`.
Each variant of this instruction (`ADD A`, `ADD B`, `ADD H`, ...) is a separate
opcode.

To disable the testing of a particular instruction for some reason, modify the
Enabled field (first field of each entry) in `lib/instructions.h`.

For a full list of options, run `./gbit -h`.


### Dependencies

This project does not have any dependencies except for a C compiler and make. On
Debian-based systems you can install these using the following command:

    $ sudo apt install build-essential


# Limitations

- The framework does currently not check the timings (i.e., how many cycles an
  instruction takes).
- This project does not currently work correctly on big-endian host
  architectures due to the union/struct layout of register state.
