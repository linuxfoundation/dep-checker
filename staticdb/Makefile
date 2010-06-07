default: staticdb.sqlite

staticdb:
	rm -f staticdb_tmp
	(for p in /lib /usr/lib; do \
	   find $$p -type f -name '*.so*' -print; done) | \
	   egrep '\.so(\.[[:digit:]]+)*$$' > liblist
	for lib in $$(cat liblist); do \
	    libname=$$(basename $$lib); \
	    objdump -T $$lib | fgrep .text | awk '{ print $$7 }' | \
	      (while read s; do echo "$$s:$$libname"; done) >> staticdb_tmp; \
	done
	egrep -v '^:' staticdb_tmp | sort | uniq > staticdb
	rm liblist staticdb_tmp

staticdb.sqlite: staticdb
	./sqliteize

clean:
	rm -f staticdb staticdb.sqlite
