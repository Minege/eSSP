LIBS=-lstdc++ -lpthread

UNAME := $(shell uname)

ifeq ($(UNAME), Darwin)
LINK = -Wl,-all_load,-install_name,libessp.so.1
else
LINK = -Wl,-soname,libessp.so.1
endif

.PHONY: clean

libessp.so:

%.o:%.c
	$(CC) -c -fPIC -ggdb -g3 -o $@ $^

libessp.so: init.o ssp_helpers.o linux.o lib/bin/libitlssp.a
	$(CC) -shared -fPIC -ggdb -g3 $(LINK) -o $@ $^

lib/bin/libitlssp.a:
	mkdir -p lib/bin/shared
	$(MAKE) -C lib

clean:
	rm -f *.o *.so
