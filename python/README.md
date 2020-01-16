# GBIT Python wrapper

This directory contains a Python (3.6+) wrapper for the GBIT library. The file
`gbit.py` calls into the shared library through ctypes, and provides all
required data types. It is recommended to use `example.py` as a starting point,
as this implements all boilerplate, and documents behavior that should be
implemented based on the CPU to be tested.

The interface and usage of this wrapper are very similar to that of the
C version. The `gbit.py` file contains all required data types, which map
directly to their C counterparts. The `GBIT` class wraps all low-level details,
and its `run` method behaves similarly to `tester_run`, where four callback
functions should be provided.

For memory accesses, two methods are provided: `GBIT.mem_write` and
`GBIT.mem_read`. Users should not fill in the memory accesses fields of the
state struct themselves. Unlike its C counterpart, the `init` callback does not
receive any arguments, as this behavior is implemented by the `GBIT` class
(e.g., the instruction memory through `GBIT.mem_read`).
