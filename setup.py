#!/usr/bin/python3
from setuptools import setup, find_packages
import importlib
kidiff = importlib.import_module("kicad-diff")

# Use the README.md as a long description.
# Note this is also included in the MANIFEST.in
with open('README.md', encoding='utf-8') as f:
    long_description = '\n' + f.read()

setup(name='kidiff',
      version=kidiff.__version__,
      description='KiCad PCB/SCH Diff',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author=kidiff.__author__,
      author_email=kidiff.__email__,
      url=kidiff.__url__,
      # Packages are marked using __init__.py
      packages=find_packages(),
      scripts=['kicad-diff-init.py', 'kicad-diff.py', 'kicad-git-diff.py'],
      install_requires=['kiauto'],
      include_package_data=True,
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                   'Natural Language :: English',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
                   ],
      platforms='POSIX',
      license='GPL-2',
      python_requires='>=3.4',
      )
