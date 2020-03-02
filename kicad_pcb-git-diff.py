#!/usr/bin/env python3
"""KiCad PCB diff tool

This program is a git plug-in to generate diffs between two KiCad PCBs.
It relies on kicad_pcb-diff.py script (where the real work is done).
"""
__author__   ='Salvador E. Tropea'
__copyright__='Copyright 2020, INTI'
__credits__  =['Salvador E. Tropea','Jesse Vincent']
__license__  ='GPL 2.0'
__version__  ='1.0.0'
__email__    ='salvador@inti.gob.ar'
__status__   ='beta'
# PCB diff tool

from os.path import (isfile,isdir,basename,sep,dirname,realpath)
from os import (getcwd,mkdir)
from sys import (exit)
from subprocess import (call)
import argparse
import logging

# Exit error codes
OLD_PCB_INVALID=1
NEW_PCB_INVALID=2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='KiCad PCB diff wrapper for Git')

    parser.add_argument('old_pcb_name',help='PCB name')
    parser.add_argument('old_pcb_file',help='Original PCB file')
    parser.add_argument('old_pcb_hash',help='Original PCB hash')
    parser.add_argument('old_pcb_perm',help='Original PCB perms')
    parser.add_argument('new_pcb_file',help='New PCB file')
    parser.add_argument('new_pcb_hash',help='New PCB hash')
    parser.add_argument('new_pcb_perm',help='New PCB perms')

    parser.add_argument('--resolution',nargs=1,help='Image resolution in DPIs [150]',default=['150'])
    parser.add_argument('--verbose','-v',action='count',default=0)
    parser.add_argument('--version',action='version', version='%(prog)s '+__version__+' - '+
                        __copyright__+' - License: '+__license__)

    args=parser.parse_args()

    # Create a logger with the specified verbosity
    if args.verbose>=2:
       log_level=logging.DEBUG
       verb='-vv'
    elif args.verbose==1:
       log_level=logging.INFO
       verb='-v'
    else:
       verb=None
       log_level=logging.WARNING
    logging.basicConfig(level=log_level)
    logger=logging.getLogger(basename(__file__))

    # Check the arguments
    old_pcb=args.old_pcb_file
    if not isfile(old_pcb):
       logger.error('%s isn\'t a valid file name' % old_pcb)
       exit(OLD_PCB_INVALID)

    new_pcb=args.new_pcb_file
    if not isfile(new_pcb):
       logger.error('%s isn\'t a valid file name' % new_pcb)
       exit(NEW_PCB_INVALID)

    resolution=int(args.resolution[0])

    # The script is invoked by git from the root of the repo
    dir_git=getcwd()+sep+'.git'
    dir_cache=None
    if not isdir(dir_git):
       logger.error('can\'t find the git repo (no '+dir_git+')')
    else:
       dir_cache=dir_git+sep+'kicad_pcb-git-cache'
       if not isdir(dir_cache):
          try:
              mkdir(dir_cache)
          except OSError:
              logger.error('can\'t create cache dir ('+dir_cache+')')
              dir_cache=None

    command=[dirname(realpath(__file__))+sep+'kicad_pcb-diff.py','--resolution',str(resolution),
             '--old_pcb_hash',args.old_pcb_hash,'--new_pcb_hash',args.new_pcb_hash]
    if verb!=None:
       command.append(verb)
    if dir_cache!=None:
       command.append('--cache_dir')
       command.append(dir_cache)
    if isfile('.kicad_pcb-git-diff'):
       command.append('--exclude')
       command.append('.kicad_pcb-git-diff')
    command.append(old_pcb)
    command.append(new_pcb)
    logger.debug(command)
    call(command)



