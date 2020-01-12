BINNAME = gbit
TARGET_SOURCES = main.c test_cpu.c
TESTER_SOURCES = lib/tester.c lib/inputstate.c lib/ref_cpu.c lib/disassembler.c

BDIR := build

CFLAGS   := -O2 -Wall -Wextra -g -MMD -I.
CXXFLAGS := -O2 -Wall -Wextra -g -MMD -I.
LDLIBS   :=

SOURCES := $(TESTER_SOURCES) $(TARGET_SOURCES)
OBJS    := $(patsubst %.c,$(BDIR)/%.o,$(patsubst %.cpp,$(BDIR)/%.o,$(SOURCES)))


# Verbosity control
ifndef V
	LOG=@printf "\e[1;32m%s\e[0m $@\n"
	MAKEFLAGS += --silent
else
	LOG=@true
endif

.SUFFIXES: # Disable builtin rules
.PHONY: all run clean

all: $(BINNAME)

run: $(BDIR)/$(BINNAME)
	-$(BDIR)/$(BINNAME)

$(BDIR)/%.o: %.c | $(BDIR)
	$(LOG) [CC]
	$(CC) $(CFLAGS) -c -o $@ $<
$(BDIR)/%.o: %.cpp | $(BDIR)
	$(LOG) [CXX]
	$(CXX) $(CXXFLAGS) -c -o $@ $<
$(BINNAME): $(OBJS) | $(BDIR)
	$(LOG) [LINK]
	$(CXX) $^ -o $@ $(LDLIBS)

$(BDIR):
	mkdir -p $@/lib

clean:
	@$(RM) -rf $(BDIR)
	@$(RM) -rf $(BINNAME)

-include $(BDIR)/*.d
-include $(BDIR)/lib/*.d
