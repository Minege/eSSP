LIBS=-lstdc++ -lpthread

.PHONY: clean

libessp.so:

%.o:%.c
	$(CC) -c -fPIC -ggdb -g3 -o $@ $^

libessp.so: init.o ssp_helpers.o linux.o lib/bin/libitlssp.a
	$(CC) -shared -fPIC -ggdb -g3 -Wl,-soname,libessp.so.1 -o $@ $^

lib/bin/libitlssp.a:
	$(MAKE) -C lib

clean:
	rm -f *.o *.so
