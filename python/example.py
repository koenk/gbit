import argparse
import signal
import sys

from gbit import GBIT, State, Regs16


def init():
    # ... Initialize your CPU here (optional) ...
    pass


def set_state(state):
    # ... Load your CPU with state as described (e.g., registers) ... */
    pass


def get_state():
    # ... Return your current CPU state ...

    state = State(
            PC = 0xdead,
            SP = 0xbeef,
            reg16 = Regs16(
                AF = 0x1122,
                BC = 0x3344,
                DE = 0x5566,
                HL = 0x7788,
            ),
            halted = True,
            interrupts_master_enabled = False,
        )
    return state


def step():
    cycles = 0

    # ... Execute a single instruction in your CPU ... */

    # Perform reads from memory like this
    #inst = gbit.mem_read(pc)

    # And write to memory like this
    #gbit.mem_write(0x1234, 0x56)

    return cycles


def sigint_handler(signum, frame):
    # KeyboardInterrupt exceptions are eaten by ctypes
    sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Game Boy Instruction Tester')
    parser.add_argument('-k', '--keep-going', action='store_true',
            default=False, help='Skip to the next instruction on a mismatch.')
    parser.add_argument('-c', '--no-enable-cb', action='store_false',
            default=True, help='Disable testing of CB prefixed instructions.',
            dest='enable_cb')
    parser.add_argument('-p', '--print-inst', action='store_true',
            default=False, help='Print instruction undergoing tests.')
    parser.add_argument('-v', '--print-input', action='store_true',
            default=False, help='Print every inputstate that is tested.')

    args = parser.parse_args()

    signal.signal(signal.SIGINT, sigint_handler)

    gbit = GBIT(init_cb=init, set_state_cb=set_state, get_state_cb=get_state,
            step_cb=step)
    gbit.run(keep_going_on_mismatch=args.keep_going,
             enable_cb_instructions=args.enable_cb,
             print_tested_instruction=args.print_inst,
             print_verbose_inputs=args.print_input)
