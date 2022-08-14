#!/usr/bin/make
prefix=/usr/local

all:

deb:
	fakeroot dpkg-buildpackage -uc -b

deb_clean:
	fakeroot debian/rules clean

install:
	install -D kicad-diff.py $(DESTDIR)$(prefix)/bin/kicad-diff.py
	install -D kicad-git-diff.py $(DESTDIR)$(prefix)/bin/kicad-git-diff.py
	install -D kicad-diff-init.py $(DESTDIR)$(prefix)/bin/kicad-diff-init.py

clean:

distclean: clean

uninstall:
	-rm -f $(DESTDIR)$(prefix)/bin/kicad-diff.py
	-rm -f $(DESTDIR)$(prefix)/bin/kicad-git-diff.py
	-rm -f $(DESTDIR)$(prefix)/bin/kicad-diff-init.py

.PHONY: all install clean distclean uninstall deb deb_clean
