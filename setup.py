#!/usr/bin/python3
import re
from setuptools import setup, find_packages


with open("kicad-diff.py", 'rt') as f:
    txt = f.read()
    version = re.search(r"__version__ = '(.*)'", txt).group(1)
    author = re.search(r"__author__ = '(.*)'", txt).group(1)
    email = re.search(r"__email__ = '(.*)'", txt).group(1)
    url = re.search(r"__url__ = '(.*)'", txt).group(1)

# Use the README.md as a long description.
# Note this is also included in the MANIFEST.in
with open('README.md', encoding='utf-8') as f:
    long_description = '\n' + f.read()

setup(name='kidiff',
      version=version,
      description='KiCad PCB/SCH Diff',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author=author,
      author_email=email,
      url=url,
      # Packages are marked using __init__.py
      packages=find_packages(),
      scripts=['kicad-diff-init.py', 'kicad-diff.py', 'kicad-git-diff.py'],
      install_requires=['kiauto'],
      include_package_data=True,
      classifiers=['Development Status :: 5 - Production/Stable',
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
