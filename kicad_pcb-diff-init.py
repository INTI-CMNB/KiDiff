#!/usr/bin/env python3
"""KiCad PCB diff tool

This program initializes a repo to use the kicad_pcb-git-diff plug-in.
"""
__author__   ='Salvador E. Tropea'
__copyright__='Copyright 2020, INTI'
__credits__  =['Salvador E. Tropea']
__license__  ='GPL 2.0'
__version__  ='1.1.0'
__email__    ='salvador@inti.gob.ar'
__status__   ='beta'

from os.path import (isfile,isdir,basename,sep,dirname,realpath)
from os import (getcwd)
from shutil import (which)
from sys import (exit)
from subprocess import (call)
import argparse
import logging
import re

# Exit error codes
NO_GIT_ROOT=1
MISSING_GIT=2
MISSING_SCRIPTS=3

git_attributes='.gitattributes'
git_config='.gitconfig'
layers_file='.kicad_pcb-git-diff'

def CheckAttributes():
    if not isfile(git_attributes):
       logger.debug('No '+git_attributes)
       return False
    attr_file=open(git_attributes,"r")
    for line in attr_file:
        if re.match('^\*.kicad_pcb\s+diff',line):
           attr_file.close()
           return True
    attr_file.close()
    return False

def CheckCommand():
    if not isfile(git_config):
       logger.debug('No '+git_config)
       return False
    cfg_file=open(git_config,"r")
    for line in cfg_file:
        if re.match('^\[diff\s+\"kicad_pcb_diff\"',line):
           cfg_file.close()
           return True
    cfg_file.close()
    return False

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='KiCad PCB diff GIT repo initialization')

    parser.add_argument('--verbose','-v',action='count',default=0)
    parser.add_argument('--version','-V',action='version', version='%(prog)s '+__version__+' - '+
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

    # Check the environment
    if which('git')==None:
       logger.error('No git command, install it')
       exit(MISSING_GIT)
    if which('kicad_pcb-git-diff.py')==None:
       logger.error('Please install the diff scripts first')
       exit(MISSING_SCRIPTS)

    # The script must be invoked from the root of the repo
    dir_git=getcwd()+sep+'.git'
    if not isdir(dir_git):
       logger.error('Run this script from the root of your repo (no .git/ here)')
       exit(NO_GIT_ROOT)

    # Configure the repo to use a local .gitconfig file
    logger.info('Configuring git to use ".gitconfig" as a configuration file')
    command=['git','config','--local','include.path','../'+git_config]
    logger.debug(command)
    call(command)

    # Add an attribute for *.kicad_pcb files
    if CheckAttributes():
       logger.info('KiCad PCB files already has a diff tool associated')
    else:
       logger.info('Associating the KiCad PCB extension to a diff plug-in')
       attr_file=open(git_attributes,"a+")
       attr_file.write("*.kicad_pcb diff=kicad_pcb_diff\n")
       attr_file.close()

    # Add a command to the new attribute
    if CheckCommand():
       logger.info('Command already configured')
    else:
       logger.info('Defining a command to compute a diff between KiCad PCB files')
       cfg_file=open(git_config,"a+")
       cfg_file.write("[diff \"kicad_pcb_diff\"]\n")
       cfg_file.write("\tcommand="+which('kicad_pcb-git-diff.py')+" -v\n")
       cfg_file.close()

    # Add a list of layers to be excluded
    if isfile(layers_file):
       logger.info('Layer exclusion file already present')
    else:
       logger.info('Generating a list of layers to be excluded')
       layer_file=open(layers_file,"w+")
       layer_file.write("B.Adhes\n")
       layer_file.write("F.Adhes\n")
       layer_file.write("#B.Paste\n")
       layer_file.write("#F.Paste\n")
       layer_file.write("#B.SilkS\n")
       layer_file.write("#F.SilkS\n")
       layer_file.write("#B.Mask\n")
       layer_file.write("#F.Mask\n")
       layer_file.write("#Dwgs.User\n")
       layer_file.write("Cmts.User\n")
       layer_file.write("Eco1.User\n")
       layer_file.write("Eco2.User\n")
       layer_file.write("Edge.Cuts\n")
       layer_file.write("Margin\n")
       layer_file.write("#B.CrtYd\n")
       layer_file.write("#F.CrtYd\n")
       layer_file.write("#B.Fab\n")
       layer_file.write("#F.Fab\n")
       layer_file.close()

