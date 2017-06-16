# -*- mode: Makefile; -*-
# -----------------------------------------
# project itlssp






CFLAGS_C = $(filter-out -include "sdk.h",$(CFLAGS))

# -----------------------------------------

# MAKE_DEP = -MMD -MT $@ -MF $(@:.o=.d)

CFLAGS = -Wall 
INCLUDES = 
LDFLAGS =  -s
RCFLAGS = 
LDLIBS = $(T_LDLIBS)  -lpthread
#LDLIBS = $(T_LDLIBS)  -lstdc++ -lpthread


LINK_exe = gcc -o $@ $^ $(LDFLAGS) $(LDLIBS)
LINK_con = gcc -o $@ $^ $(LDFLAGS) $(LDLIBS)
LINK_dll = gcc -o $@ $^ $(LDFLAGS) $(LDLIBS) -shared
LINK_lib = rm -f $@ && ar rcs $@ $^
COMPILE_c = gcc $(CFLAGS_C) -o $@ -c $< $(MAKEDEP) $(INCLUDES)
COMPILE_cpp = g++ $(CFLAGS) -o $@ -c $< $(MAKEDEP) $(INCLUDES)
COMPILE_rc = windres $(RCFLAGS) -J rc -O coff -i $< -o $@ -I$(dir $<)

%.o : %.c ; $(COMPILE_c)
%.o : %.cpp ; $(COMPILE_cpp)
%.o : %.cxx ; $(COMPILE_cpp)
%.o : %.rc ; $(COMPILE_rc)
.SUFFIXES: .o .d .c .cpp .cxx .rc

all: all.before all.targets all.after

all.before :
	-
all.after : $(FIRST_TARGET)
	
all.targets : Release_target 

clean :
	rm -fv $(clean.OBJ)
	rm -fv $(DEP_FILES)

.PHONY: all clean distclean

# -----------------------------------------
# Release_target

Release_target.BIN = bin/libitlssp.a
Release_target.LIB = bin/shared/libitlssp.so
Release_target.OBJ = Encryption.o ITLSSPProc.o Random.o SSPComs.o serialfunc.o  SSPDownload.o ssp_commands.o
DEP_FILES += Encryption.d ITLSSPProc.d Random.d SSPComs.d serialfunc.d 
clean.OBJ += $(Release_target.BIN) $(Release_target.OBJ) $(Release_target.LIB)

Release_target : Release_target.before $(Release_target.BIN) $(Release_target.LIB) Release_target.after_always
Release_target : CFLAGS += -O2  -Os -fPIC
Release_target : INCLUDES += 
Release_target : RCFLAGS += 
Release_target : LDFLAGS += -s   $(CREATE_DEF)
Release_target : T_LDLIBS = 
ifdef LMAKE
Release_target : CFLAGS -= -O1 -O2 -g -pipe
endif

Release_target.before :
	
	
Release_target.after_always : $(Release_target.BIN)
	
$(Release_target.BIN) : $(Release_target.OBJ)
	$(LINK_lib)
$(Release_target.LIB) : $(Release_target.OBJ)
	$(LINK_dll)
	
ifdef MAKE_DEP
-include $(DEP_FILES)
endif
