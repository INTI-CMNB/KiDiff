#!/usr/bin/make
prefix=/usr/local

all:

install:
	install -D kicad_pcb-diff.py $(DESTDIR)$(prefix)/bin/kicad_pcb-diff.py
	install -D kicad_pcb-git-diff.py $(DESTDIR)$(prefix)/bin/kicad_pcb-git-diff.py
	install -D kicad_pcb-diff-init.py $(DESTDIR)$(prefix)/bin/kicad_pcb-diff-init.py

clean:

distclean: clean

uninstall:
	-rm -f $(DESTDIR)$(prefix)/bin/kicad_pcb-diff.py
	-rm -f $(DESTDIR)$(prefix)/bin/kicad_pcb-git-diff.py
	-rm -f $(DESTDIR)$(prefix)/bin/kicad_pcb-diff-init.py

.PHONY: all install clean distclean uninstall

