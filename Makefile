# Binary and target CPU - add your source files here
BINNAME = gbit
BINSRC = main.c test_cpu.c

# Test framework (shared library)
LIBNAME = libgbit.so
LIBSRC = lib/tester.c lib/inputstate.c lib/ref_cpu.c lib/disassembler.c

# Build directory - stores intermediate object files
BDIR := build

CURDIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

CFLAGS   := -O2 -Wall -Wextra -g -MMD -I. -fPIC
CXXFLAGS := -O2 -Wall -Wextra -g -MMD -I. -fPIC
LDFLAGS  := -Wl,-rpath="$(CURDIR)" -L. -lgbit

LIBOBJS := $(patsubst %.c,$(BDIR)/%.o,$(LIBSRC))
BINOBJS := $(patsubst %.c,$(BDIR)/%.o,$(patsubst %.cpp,$(BDIR)/%.o,$(BINSRC)))


# Verbosity control
ifndef V
	LOG=@printf "\e[1;32m%s\e[0m $@\n"
	MAKEFLAGS += --silent
else
	LOG=@true
endif

.SUFFIXES: # Disable builtin rules
.PHONY: all run clean

all: $(LIBNAME) $(BINNAME)

run: $(BDIR)/$(BINNAME)
	-$(BDIR)/$(BINNAME)

$(BDIR)/%.o: %.c | $(BDIR)
	$(LOG) [CC]
	$(CC) $(CFLAGS) -c -o $@ $<
$(BDIR)/%.o: %.cpp | $(BDIR)
	$(LOG) [CXX]
	$(CXX) $(CXXFLAGS) -c -o $@ $<
$(LIBNAME): $(LIBOBJS) | $(BDIR)
	$(LOG) [LINK]
	$(CC) $^ -o $@ -shared
$(BINNAME): $(BINOBJS) | $(LIBNAME) $(BDIR)
	$(LOG) [LINK]
	$(CXX) $^ -o $@ $(LDFLAGS)

$(BDIR):
	mkdir -p $@/lib

clean:
	@$(RM) -rf $(BDIR)
	@$(RM) -rf $(BINNAME)
	@$(RM) -rf $(LIBNAME)

-include $(BDIR)/*.d
-include $(BDIR)/lib/*.d
