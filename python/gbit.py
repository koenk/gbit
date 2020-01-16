#
# Python interface for the GBIT testing framework. This interface calls into
# libgbit.so via Python's ctypes module
#
# The GBIT class exposes a Python-friendly interface that can be used for
# testing Game Boy CPUs implemented in Python.
#
# Developers should use the State and Regs8/Regs16 classes for transferring Game
# Boy CPU state to and from the GBIT class callbacks; all other types defined in
# this module can be ignored.
#

import os

from ctypes import *


class MemAccess(Structure):
    TYPE_WRITE = 1

    _fields_ = [
        ('type',    c_int),
        ('addr',    c_uint16),
        ('val',     c_uint8),
    ]


class Regs16(Structure):
    _fields_ = [
        ('AF', c_uint16),
        ('BC', c_uint16),
        ('DE', c_uint16),
        ('HL', c_uint16),
    ]

    def __repr__(self):
        return f'<Reg16 AF={self.AF:04x} BC={self.BC:04x} DE={self.DE:04x} ' + \
               f'HL={self.HL:04x}>'


class Regs8(Structure):
    _fields_ = [
        ('F', c_uint8), ('A', c_uint8),
        ('C', c_uint8), ('B', c_uint8),
        ('E', c_uint8), ('D', c_uint8),
        ('L', c_uint8), ('H', c_uint8),
    ]

    def __repr__(self):
        return f'<Reg8 A={self.A:02x} F={self.F:02x} B={self.B:02x} ' + \
               f'C={self.C:02x} D={self.D:02x} E={self.E:02x} ' + \
               f'H={self.H:02x} L={self.L:02x}>'


class RegsUnion(Union):
    _fields_ = [
        ('reg16', Regs16),
        ('reg8',  Regs8),
    ]

    def __repr__(self):
        return f'<CRegsUnion reg16={self.reg16} reg8={self.reg8}>'


class State(Structure):
    _anonymous_ = ('regs',)
    _fields_ = [
        ('regs',                        RegsUnion),
        ('SP',                          c_uint16),
        ('PC',                          c_uint16),
        ('halted',                      c_bool),
        ('interrupts_master_enabled',   c_bool),
        ('num_mem_accesses',            c_int),
        ('mem_accesses',                MemAccess * 16),
    ]

    def __repr__(self):
        return f'<CState {self.regs} SP={self.SP:04x} PC={self.PC:04x} ' + \
               f'hlt={self.halted} ime={self.interrupts_master_enabled} ' + \
               f'num_mem_accesses={self.num_mem_accesses}>'
    def __str__(self):
        return ' PC   SP   AF   BC   DE   HL  ZNHC hlt IME\n' + \
               '%04x %04x %04x %04x %04x %04x %d%d%d%d  %d   %d\n' % \
               (self.PC, self.SP, self.reg16.AF, self.reg16.BC, self.reg16.DE,
                self.reg16.HL, bit(self.reg8.F, 7), bit(self.reg8.F, 6),
                bit(self.reg8.F, 5), bit(self.reg8.F, 4), self.halted,
                self.interrupts_master_enabled)


# Types of the callback functions
init_cb_type = CFUNCTYPE(None, c_size_t, POINTER(c_uint8))
set_state_cb_type = CFUNCTYPE(None, POINTER(State))
get_state_cb_type = CFUNCTYPE(None, POINTER(State))
step_cb_type = CFUNCTYPE(None)


class Operations(Structure):
    _fields_ = [
        ('init',        init_cb_type),
        ('set_state',   set_state_cb_type),
        ('get_state',   get_state_cb_type),
        ('step',        step_cb_type)
    ]


class Flags(Structure):
    _fields_ = [
        ('keep_going_on_mismatch',          c_bool),
        ('enable_cb_instruction_testing',   c_bool),
        ('print_tested_instruction',        c_bool),
        ('print_verbose_inputs',            c_bool)
    ]


class GBIT:
    def __init__(self, libname='./libgbit.so', init_cb=None, set_state_cb=None,
            get_state_cb=None, step_cb=None):
        self.libname = libname
        self.init_cb = init_cb
        self.set_state_cb = set_state_cb
        self.get_state_cb = get_state_cb
        self.step_cb = step_cb

        self.mem_writes = []
        self.lib = None
        self.instruction_mem_size = 0
        self.instruction_mem_ptr = None

        self.c_init_cb = init_cb_type(self._init_cb)
        self.c_set_state_cb = set_state_cb_type(self._set_state_cb)
        self.c_get_state_cb = get_state_cb_type(self._get_state_cb)
        self.c_step_cb = step_cb_type(self._step_cb)


    def load_library(self):
        if self.lib:
            return
        if not os.path.exists(self.libname):
            raise Exception(f'Could not find library {self.libname}. Make '
                    'sure you are executing this from the correct directory, '
                    'or pass the correct path.')
        self.lib = cdll.LoadLibrary(self.libname)
        self.lib.tester_run.argtypes = [POINTER(Flags), POINTER(Operations)]
        self.lib.tester_run.restype = c_int

    def run(self, keep_going_on_mismatch=False, enable_cb_instructions=True,
            print_tested_instruction=False, print_verbose_inputs=False):

        flags = Flags(
                    keep_going_on_mismatch=keep_going_on_mismatch,
                    enable_cb_instruction_testing=enable_cb_instructions,
                    print_tested_instruction=print_tested_instruction,
                    print_verbose_inputs=print_verbose_inputs,
                )

        ops = Operations(self.c_init_cb, self.c_set_state_cb,
                self.c_get_state_cb, self.c_step_cb)

        self.load_library()
        self.lib.tester_run(pointer(flags), pointer(ops))

    def mem_write(self, address, value):
        self.mem_writes.append((address, value))

    def mem_read(self, address):
        #print("MEMREAD", repr(address), self.instruction_mem_size)
        #print("READ", self.instruction_mem_ptr[address])
        if address < self.instruction_mem_size:
            return self.instruction_mem_ptr[address]
        else:
            return 0xaa

    def _init_cb(self, size, mem):
        self.instruction_mem_size = size
        self.instruction_mem_ptr = mem
        if self.init_cb:
            self.init_cb()

    def _set_state_cb(self, state):
        self.mem_writes = []
        self.set_state_cb(state.contents)

    def _get_state_cb(self, ret_state):
        py_state = self.get_state_cb()

        ret_state.contents.PC = py_state.PC
        ret_state.contents.SP = py_state.SP
        ret_state.contents.reg16.AF = py_state.reg16.AF
        ret_state.contents.reg16.BC = py_state.reg16.BC
        ret_state.contents.reg16.DE = py_state.reg16.DE
        ret_state.contents.reg16.HL = py_state.reg16.HL
        ret_state.contents.halted = py_state.halted
        ret_state.contents.interrupts_master_enabled = \
                py_state.interrupts_master_enabled
        ret_state.contents.num_mem_accesses = len(self.mem_writes)
        for i, (addr, val) in enumerate(self.mem_writes):
            ret_state.contents.mem_accesses[i].type = MemAccess.TYPE_WRITE
            ret_state.contents.mem_accesses[i].addr = addr
            ret_state.contents.mem_accesses[i].val = val

    def _step_cb(self):
        return self.step_cb()


def bit(val, bitpos):
    return ((val) >> (bitpos)) & 1
