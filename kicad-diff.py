#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnologïa Industrial
# License: GPL-2.0
# Project: KiCad Diff
# Adapted from: https://github.com/obra/kicad-tools
"""
KiCad PCB/SCH diff tool

This program generates a PDF file showing the changes between two KiCad PCB
files.
PCBs are plotted into PDF files, one for each layer. Then ImageMagick is used
to compare the layers and JPG files are generated. The JPGs are finally
assembled into one PDF file and the default PDF reader is invoked.
All the intermediate files are generated in the system temporal directory and
removed as soon as the job is finished. You can cache the layers PDFs
specifying a cache directory and keep the resulting diff images specifying an
output directory.
The default resolution for the images is 150 DPI. It can be increased for
better images, at the cost of (exponetially) longer execution times. You can
provide a smaller resolution for faster processing. For high resolution you
could need to configure the ImageMagick limits. Consult the 'identify -list
resource' command.
For the SCHs we use KiAuto.

"""
__author__ = 'Salvador E. Tropea'
__copyright__ = 'Copyright 2020-2022, INTI/'+__author__
__credits__ = ['Salvador E. Tropea', 'Jesse Vincent']
__license__ = 'GPL 2.0'
__version__ = '2.2.0'
__email__ = 'salvador@inti.gob.ar'
__status__ = 'beta'
__url__ = 'https://github.com/INTI-CMNB/KiDiff/'

import argparse
import atexit
from glob import glob
from hashlib import sha1
import logging
from os.path import isfile, isdir, basename, sep, splitext, abspath
from os import makedirs, rename, remove
from pcbnew import LoadBoard, PLOT_CONTROLLER, FromMM, PLOT_FORMAT_PDF, Edge_Cuts, GetBuildVersion
import re
from shutil import rmtree, which
from subprocess import call, PIPE, run, STDOUT, CalledProcessError
from sys import exit
from tempfile import mkdtemp
import time

# Exit error codes
# Fixed values
INTERNAL_ERROR = 1
ARGS_ERROR = 2
# Our values
FAILED_TO_PLOT = 3
MISSING_TOOLS = 4
FAILED_TO_CONVERT = 5
FAILED_TO_DIFF = 6
FAILED_TO_JOIN = 7
WRONG_EXCLUDE = 8
WRONG_ARGUMENT = 9
DIFF_TOO_BIG = 10
OLD_INVALID = 11
NEW_INVALID = 12
kicad_version_major = kicad_version_minor = kicad_version_patch = 0
is_pcb = True
use_poppler = True


def GenPCBImages(file, file_hash, hash_dir, file_no_ext, layer_names):
    # Setup the KiCad plotter
    board = LoadBoard(file)
    pctl = PLOT_CONTROLLER(board)
    popt = pctl.GetPlotOptions()
    popt.SetOutputDirectory(abspath(hash_dir))  # abspath: Otherwise it will be relative to the file
    # Options
    popt.SetPlotFrameRef(False)
    # KiCad 5 only
    if kicad_version_major == 5:
        popt.SetLineWidth(FromMM(0.35))
    popt.SetAutoScale(True)
    popt.SetScale(0)
    popt.SetMirror(False)
    popt.SetUseGerberAttributes(True)
    popt.SetExcludeEdgeLayer(False)
    popt.SetUseAuxOrigin(False)
    popt.SetSkipPlotNPTH_Pads(False)
    popt.SetPlotViaOnMaskLayer(True)
    popt.SetSubtractMaskFromSilk(False)

    # Plot all used layers to PDF files
    for i, layer in layer_names.items():
        layer_rep = layer.replace('.', '_')
        name_pdf_kicad = '{}{}{}-{}.pdf'.format(hash_dir, sep, file_no_ext, layer_rep)
        name_pdf = '{}{}{}.pdf'.format(hash_dir, sep, layer_rep)
        # Create the PDF, or use a cached version
        if not isfile(name_pdf):
            logger.info('Plotting %s layer' % layer)
            pctl.SetLayer(i)
            pctl.OpenPlotfile(layer, PLOT_FORMAT_PDF, layer)
            pctl.PlotLayer()
            pctl.SetLayer(Edge_Cuts)
            pctl.PlotLayer()
            pctl.ClosePlot()
            if not isfile(name_pdf_kicad):
                logger.error('Failed to plot %s' % name_pdf_kicad)
                exit(FAILED_TO_PLOT)
            rename(name_pdf_kicad, name_pdf)
        else:
            logger.debug('Using cached %s layer' % layer)


def GenSCHImage(file, file_hash, hash_dir, file_no_ext, layer_names, all):
    name_pdf = '{}{}{}.pdf'.format(hash_dir, sep, layer_names[0])
    # Create the PDF, or use a cached version
    if not isfile(name_pdf):
        logger.info('Plotting the schematic')
        cmd = ['eeschema_do', 'export', '--file_format', 'pdf', '--monochrome', '--no_frame', '--output_name', name_pdf]
        if all:
            cmd.append('--all_pages')
        cmd.extend([file, '.'])
        logger.debug('Executing: '+str(cmd))
        call(cmd)
        if not isfile(name_pdf):
            logger.error('Failed to plot %s' % name_pdf)
            exit(FAILED_TO_PLOT)
    else:
        logger.debug('Using cached schematic')


def GenImages(file, file_hash, all):
    # Check if we have a valid cache
    hash_dir = cache_dir+sep+file_hash
    logger.debug('Cache for {} will be {}'.format(file, hash_dir))
    if isdir(hash_dir):
        logger.info('cache dir for `%s` already exists' % file)

    file_no_ext = splitext(basename(file))[0]

    # Read the layer names from the file
    layer_names = load_layer_names(file) if is_pcb else {0: 'Schematic_all' if args.all_pages else 'Schematic'}

    if is_pcb:
        GenPCBImages(file, file_hash, hash_dir, file_no_ext, layer_names)
    else:
        GenSCHImage(file, file_hash, hash_dir, file_no_ext, layer_names, all)
    return layer_names


def run_command(command):
    logger.debug('Executing: '+str(command))
    try:
        run(command, check=True)
    except CalledProcessError as e:
        logger.debug('Running {} returned {}'.format(e.cmd, e.returncode))
        if e.output:
            logger.debug('- StdOut from command: '+e.output.decode())
        if e.stderr:
            logger.debug('- StdErr from command: '+e.stderr.decode())


def pdf2png(base_name, blank=False, ref=None):
    source = base_name+'.pdf' if not blank else ref+'.pdf'
    dest1 = base_name+'.png'
    destm = base_name+'-0.png'
    if isfile(dest1):
        logger.debug(source+" alredy converted to PNG")
        return [dest1]
    if isfile(destm):
        logger.debug(source+" alredy converted to PNG")
        return sorted(glob(base_name+'-*.png'))
    if use_poppler:
        cmd = 'cat {} | pdftoppm -r {} -gray - | convert - {}'.format(source, resolution, dest1)
    else:
        cmd = ('convert -density {} {} -background white -alpha remove -alpha off -threshold 50% '
               '-colorspace Gray -resample {} -depth 8 {}'.format(resolution*2, source, resolution, dest1))
    run_command(['bash', '-c', cmd])
    if blank:
        # Create a blank file
        logger.debug('Blanking '+dest1)
        cmd = ('convert {} -background white -threshold 100% -negate -colorspace Gray {}'.format(dest1, dest1))
        run_command(['bash', '-c', cmd])
    if isfile(dest1):
        return [dest1]
    if isfile(destm):
        return sorted(glob(base_name+'-*.png'))
    assert False


def create_diff_stereo(old_name, new_name, diff_name, font_size, layer, resolution, name_layer):
    text = ' -font helvetica -pointsize '+font_size+' -draw "text 10,'+font_size+' \''+name_layer+'\'" '
    command = ['bash', '-c', '( convert '+new_name+' miff:- ; convert '+old_name+' miff:- ) | ' +
               r'convert - \( -clone 0-1 -compose darken -composite \) '+text+' -channel RGB -combine '+diff_name]
    run_command(command)


def create_diff_stat(old_name, new_name, diff_name, font_size, layer, resolution, name_layer):
    # Compare both
    cmd = ['compare',
           # Tolerate 5 % error in color (configurable)
           '-fuzz', str(args.fuzz)+'%',
           # Count how many pixels differ
           '-metric', 'AE',
           new_name,
           old_name,
           '-colorspace', 'RGB',
           diff_name]
    logger.debug('Executing: '+str(cmd))
    res = run(cmd, stdout=PIPE, stderr=STDOUT)
    errors = int(res.stdout.decode())
    logger.debug('AE for {}: {}'.format(layer, errors))
    if args.threshold and errors > args.threshold:
        logger.error('Difference for `{}` is not acceptable ({} > {})'.format(name_layer, errors, args.threshold))
        exit(DIFF_TOO_BIG)
    cmd = ['convert', diff_name, '-font', 'helvetica', '-pointsize', font_size, '-draw',
           'text 10,'+font_size+" '"+name_layer+"'", diff_name]
    logger.debug('Executing: '+str(cmd))
    call(cmd)


def DiffImages(old_file_hash, new_file_hash, layers_old, layers_new):
    old_hash_dir = cache_dir+sep+old_file_hash
    new_hash_dir = cache_dir+sep+new_file_hash
    files = ['convert']
    # Compute the difference between images for each layer, store JPGs
    font_size = str(int(resolution/5))
    all_layers = {}
    all_layers.update(layers_old)
    all_layers.update(layers_new)
    for i in sorted(all_layers.keys()):
        layer = all_layers[i]
        name_layer = layer if layer == 'Schematic' else 'Layer: '+layer
        layer_rep = layer.replace('.', '_')
        # Convert the PDFs to PNGs
        old_file = old_hash_dir+sep+layer_rep
        new_file = new_hash_dir+sep+layer_rep
        old = pdf2png(old_file, i not in layers_old, new_file)
        new = pdf2png(new_file, i not in layers_new, old_file)
        if i not in layers_old:
            name_layer += ' only in new file'
        if i not in layers_new:
            name_layer += ' only in old file'
        if len(old) != len(new):
            logger.error("Adding/removing sheets isn't supported yet")
            exit(FAILED_TO_DIFF)
        for i, old_name in enumerate(old):
            new_name = new[i]
            diff_name = output_dir+sep+'diff-'+layer_rep+str(i)+'.png'
            logger.info('Creating diff for '+(layer+'_'+str(i) if len(old) > 1 else layer))
            if args.diff_mode == 'red_green':
                create_diff_stereo(old_name, new_name, diff_name, font_size, layer, resolution, name_layer)
            else:
                create_diff_stat(old_name, new_name, diff_name, font_size, layer, resolution, name_layer)
            if not isfile(diff_name):
                logger.error('Failed to create diff %s' % diff_name)
                exit(FAILED_TO_DIFF)
            files.append(diff_name)
    # Join all the JPGs into one PDF
    out_name = output_dir+sep+args.output_name
    output_pdf = out_name
    # The name must end with .pdf
    if not output_pdf.endswith('.pdf'):
        output_pdf += '.pdf'
    files.append(output_pdf)
    logger.info('Joining all diffs into one PDF')
    logger.debug(files)
    call(files)
    if not isfile(output_pdf):
        logger.error('Failed to join diffs into %s' % output_pdf)
        exit(FAILED_TO_JOIN)
    # Fix the name
    if not args.output_name.endswith('.pdf'):
        logger.debug('{} -> {}'.format(output_pdf, out_name))
        rename(output_pdf, out_name)
    # Remove the individual PNGs
    if not args.keep_pngs:
        for f in files[1:-1]:
            remove(f)
    return out_name


def GetDigest(file_path):
    h = sha1()
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def CleanOutputDir():
    rmtree(output_dir)


def CleanCacheDir():
    rmtree(cache_dir)


def load_layer_names(old_file):
    layer_names = {}
    with open(old_file, "r") as file_file:
        collect_layers = False
        for line in file_file:
            if collect_layers:
                z = re.match(r'\s+\((\d+)\s+(\S+)', line)
                if z:
                    res = z.groups()
                    lname = res[1]
                    if lname[0] == '"':
                        lname = lname[1:-1]
                    lnum = res[0]
                    logger.debug(lname+'->'+lnum)
                    ilnum = int(lnum)
                    if lname not in layer_exclude and ilnum not in layer_exclude:
                        layer_names[ilnum] = lname
                    else:
                        logger.debug('Excluding layer '+res[1])
                else:
                    if re.search(r'^\s+\)$', line):
                        break
            else:
                if re.search(r'\s+\(layers', line):
                    collect_layers = True
    return layer_names


def thre_type(astr, min=0, max=1e6):
    value = int(astr)
    if min <= value <= max:
        return value
    else:
        raise argparse.ArgumentTypeError('value not in range %s-%s' % (min, max))


def get_layer(line):
    line = line.rstrip()
    try:
        line = int(line)
    except ValueError:
        pass
    return line


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KiCad diff')

    parser.add_argument('old_file', help='Original file (PCB/SCH)')
    parser.add_argument('new_file', help='New file (PCB/SCH)')
    parser.add_argument('--all_pages', help='Compare all the schematic pages', action='store_true')
    parser.add_argument('--cache_dir', help='Directory to cache images', type=str)
    parser.add_argument('--diff_mode', help='How to compute the image difference [red_green]',
                        choices=['red_green', 'stats'], default='red_green')
    parser.add_argument('--exclude', help='Exclude layers in file (one layer per line)', type=str)
    parser.add_argument('--force_gs', help='Use Ghostscript even when Poppler is available', action='store_true')
    parser.add_argument('--fuzz', help='Color tolerance for diff stats mode [%(default)s]', type=int, choices=range(0, 101),
                        default=5, metavar='[0-100]')
    parser.add_argument('--keep_pngs', help="Don't remove the individual pages", action='store_true')
    parser.add_argument('--new_file_hash', help='Use this hash for NEW_FILE', type=str)
    parser.add_argument('--no_reader', help="Don't open the PDF reader", action='store_false')
    parser.add_argument('--old_file_hash', help='Use this hash for OLD_FILE', type=str)
    parser.add_argument('--only_cache', help='Just populate the cache using OLD_FILE, no diff', action='store_true')
    parser.add_argument('--output_dir', help='Directory for the output file', type=str)
    parser.add_argument('--output_name', help='Name of the output diff', type=str, default='diff.pdf')
    parser.add_argument('--resolution', help='Image resolution in DPIs [%(default)s]', type=int, default=150)
    parser.add_argument('--threshold', help='Error threshold for diff stats mode, 0 is no error [%(default)s]',
                        type=thre_type, default=0, metavar='[0-1000000]')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--version', action='version', version='%(prog)s '+__version__+' - ' +
                        __copyright__+' - License: '+__license__)

    args = parser.parse_args()

    # Create a logger with the specified verbosity
    if args.verbose >= 2:
        log_level = logging.DEBUG
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(basename(__file__))

    # Check the environment
    if which('convert') is None:
        logger.error('No convert command, install ImageMagick')
        exit(MISSING_TOOLS)
    use_poppler = not args.force_gs
    if which('pdftoppm') is None:
        if which('gs') is None:
            logger.error('No pdftoppm or ghostscript command, install poppler-utils or ghostscript')
            exit(MISSING_TOOLS)
        use_poppler = False
    if which('xdg-open') is None:
        logger.warning('No xdg-open command, install xdg-utils. Disabling the PDF viewer.')
        args.no_reader = False

    # KiCad version
    kicad_version = GetBuildVersion()
    m = re.search(r'(\d+)\.(\d+)\.(\d+)', kicad_version)
    if m is None:
        logger.error("Unable to detect KiCad version, got: `{}`".format(kicad_version))
        exit(MISSING_TOOLS)
    kicad_version_major = int(m.group(1))
    kicad_version_minor = int(m.group(2))
    kicad_version_patch = int(m.group(3))

    # Check the arguments
    old_file = args.old_file
    if not isfile(old_file):
        logger.error('%s isn\'t a valid file name' % old_file)
        exit(OLD_INVALID)
    if args.old_file_hash:
        old_file_hash = args.old_file_hash
    else:
        old_file_hash = GetDigest(old_file)
    logger.debug('{} SHA1 is {}'.format(old_file, old_file_hash))

    new_file = args.new_file
    if not isfile(new_file) and not args.only_cache:
        logger.error('%s isn\'t a valid file name' % new_file)
        exit(NEW_INVALID)
    new_file_hash = None
    if args.new_file_hash:
        new_file_hash = args.new_file_hash
    elif not args.only_cache:
        new_file_hash = GetDigest(new_file)
    logger.debug('{} SHA1 is {}'.format(new_file, new_file_hash))

    if args.cache_dir:
        cache_dir = args.cache_dir
        if not isdir(cache_dir):
            makedirs(cache_dir, exist_ok=True)
        logger.debug('Cache dir: %s' % cache_dir)
    else:
        if args.only_cache:
            logger.error('Asking to populate the cache, but no cache dir specified')
            exit(ARGS_ERROR)
        cache_dir = mkdtemp()
        logger.debug('Temporal cache dir %s' % cache_dir)
        atexit.register(CleanCacheDir)

    if args.output_dir:
        output_dir = args.output_dir
        if not isdir(output_dir):
            makedirs(output_dir, exist_ok=True)
        logger.debug('Output dir: %s' % output_dir)
    else:
        output_dir = mkdtemp()
        logger.debug('Temporal output dir %s' % output_dir)
        atexit.register(CleanOutputDir)

    resolution = args.resolution
    if resolution < 30 or resolution > 400:
        logger.warning('Resolution outside the recommended range [30,400]')

    layer_exclude = []
    if args.exclude:
        exclude = args.exclude
        if not isfile(exclude):
            logger.error('Invalid exclude file name ('+exclude+')')
            exit(WRONG_EXCLUDE)
        with open(exclude) as f:
            layer_exclude = [get_layer(line) for line in f]
        logger.debug('%d layers to be excluded' % len(layer_exclude))

    # Are we using PCBs or SCHs?
    is_pcb = old_file.endswith('.kicad_pcb')

    if not is_pcb and which('eeschema_do') is None:
        logger.error('No eeschema_do command, install KiAuto')
        exit(MISSING_TOOLS)

    layers_old = GenImages(old_file, old_file_hash, args.all_pages)
    if args.only_cache:
        exit(0)
    layers_new = GenImages(new_file, new_file_hash, args.all_pages)

    output_pdf = DiffImages(old_file_hash, new_file_hash, layers_old, layers_new)

    if args.no_reader:
        call(['xdg-open', output_pdf])
        time.sleep(5)
