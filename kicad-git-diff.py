#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnologïa Industrial
# License: GPL-2.0
# Project: KiCad Diff
# Adapted from: https://github.com/obra/kicad-tools
"""
KiCad diff tool

This program is a git plug-in to generate diffs between two KiCad PCBs.
It relies on kicad-diff.py script (where the real work is done).
"""
__author__ = 'Salvador E. Tropea'
__copyright__ = 'Copyright 2020, INTI'
__credits__ = ['Salvador E. Tropea', 'Jesse Vincent']
__license__ = 'GPL 2.0'
__version__ = '2.4.3'
__email__ = 'salvador@inti.gob.ar'
__status__ = 'beta'
__url__ = 'https://github.com/INTI-CMNB/KiDiff/'

import argparse
import logging
from os.path import isfile, isdir, basename, sep, dirname, realpath
from os import getcwd, mkdir
from subprocess import call
from sys import exit

# Exit error codes
OLD_PCB_INVALID = 1
NEW_PCB_INVALID = 2

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KiCad diff wrapper for Git')

    parser.add_argument('old_file_name', help='PCB/SCH name')
    parser.add_argument('old_file_file', help='Original PCB/SCH file')
    parser.add_argument('old_file_hash', help='Original PCB/SCH hash')
    parser.add_argument('old_file_perm', help='Original PCB/SCH perms')
    parser.add_argument('new_file_file', help='New PCB/SCH file')
    parser.add_argument('new_file_hash', help='New PCB/SCH hash')
    parser.add_argument('new_file_perm', help='New PCB/SCH perms')

    parser.add_argument('--resolution', nargs=1, help='Image resolution in DPIs [150]', default=['150'])
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--version', action='version', version='%(prog)s '+__version__+' - ' +
                        __copyright__+' - License: '+__license__)

    args = parser.parse_args()

    # Create a logger with the specified verbosity
    if args.verbose >= 2:
        log_level = logging.DEBUG
        verb = '-vv'
    elif args.verbose == 1:
        log_level = logging.INFO
        verb = '-v'
    else:
        verb = None
        log_level = logging.WARNING
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(basename(__file__))

    # Check the arguments
    old_file = args.old_file_file
    if not isfile(old_file):
        logger.error('%s isn\'t a valid file name' % old_file)
        exit(OLD_PCB_INVALID)

    new_file = args.new_file_file
    if not isfile(new_file):
        logger.error('%s isn\'t a valid file name' % new_file)
        exit(NEW_PCB_INVALID)

    resolution = int(args.resolution[0])

    # The script is invoked by git from the root of the repo
    dir_git = getcwd()+sep+'.git'
    dir_cache = None
    if not isdir(dir_git):
        logger.error('can\'t find the git repo (no '+dir_git+')')
    else:
        dir_cache = dir_git+sep+'kicad-git-cache'
        if not isdir(dir_cache):
            try:
                mkdir(dir_cache)
            except OSError:
                logger.error('can\'t create cache dir ('+dir_cache+')')
                dir_cache = None

    command = [dirname(realpath(__file__))+sep+'kicad-diff.py', '--resolution', str(resolution),
               '--old_file_hash', args.old_file_hash]
    if int(args.new_file_hash, 16):
        # When we compare to the currently modified file git uses 0 as hash
        # If we use it all files that we didn't yet commit become the same
        command += ['--new_file_hash', args.new_file_hash]
    if verb is not None:
        command.append(verb)
    if dir_cache is not None:
        command.append('--cache_dir')
        command.append(dir_cache)
    if isfile('.kicad-git-diff'):
        command.append('--exclude')
        command.append('.kicad-git-diff')
    command.append(old_file)
    command.append(new_file)
    logger.debug(command)
    call(command)
