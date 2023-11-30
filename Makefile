#!/usr/bin/make
PYTEST?=pytest-3
prefix?=/usr/local

all:

deb:
	DEB_BUILD_OPTIONS=nocheck fakeroot dpkg-buildpackage -uc -b

deb_clean:
	fakeroot debian/rules clean

install:
	install -D kicad-diff.py $(DESTDIR)$(prefix)/bin/kicad-diff.py
	install -D kicad-git-diff.py $(DESTDIR)$(prefix)/bin/kicad-git-diff.py
	install -D kicad-diff-init.py $(DESTDIR)$(prefix)/bin/kicad-diff-init.py

test:
	rm -rf output
	$(PYTEST) --test_dir output

t1:
	rm -rf pp
	-$(PYTEST) --log-cli-level debug -k "$(SINGLE_TEST)" --test_dir pp
	@echo "********************" Output
	@cat pp/*/output.txt
	@echo "********************" Error
	@tail -n 30 pp/*/error.txt

test_server:
	pytest-3 --test_dir output

clean:

distclean: clean

uninstall:
	-rm -f $(DESTDIR)$(prefix)/bin/kicad-diff.py
	-rm -f $(DESTDIR)$(prefix)/bin/kicad-git-diff.py
	-rm -f $(DESTDIR)$(prefix)/bin/kicad-diff-init.py

.PHONY: all install clean distclean uninstall deb deb_clean
