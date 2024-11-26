# KiDiff (kicad-diff or kicad_pcb-diff)

This program generates a PDF file showing the changes between two KiCad PCB or
SCH files.

PCBs are plotted into PDF files, one for each layer. Then ImageMagick is used
to compare the layers and PNG files are generated. The PNGs are finally
assembled into one PDF file and the default PDF reader is invoked.

All the intermediate files are generated in the system temporal directory and
removed as soon as the job is finished. You can cache the layers PDFs
specifying a cache directory and keep the resulting diff images specifying an
output directory.

For SCHs the process is similar, but using KiAuto. Note that one schematic is
compared at a time. The `--all_pages` option allows comparing multiple pages.
In this case adding or removing pages is only supported when the
`rsvg-convert` tool is available. Also note that this can't be done by the git
plug-in because git extracts only the file you want to compare. Consult the
advanced use explanation.

The default resolution for the images is 150 DPI. It can be increased for
better images, at the cost of (exponentially) longer execution times. You can
provide a smaller resolution for faster processing. For high resolution you
could need to configure the ImageMagick limits. Consult the 'identify -list
resource' command.

# Installation

## Dependencies

In order to run the scripts you need:

- Python 3.5 or newer
- KiCad 5.1 or newer
- Python3 wxWidgets (i.e. python3-wxgtk4.0). This is usually installed with
  KiCad.
- ImageMagick tools (i.e. imagemagick Debian package). Used to manipulate
  images and create PDF files.
- pdftoppm tool (i.e. poppler-utils Debian package). Used to decode PDF files.
  - Alternative: Ghostscript (slower and worst results)
- rsvg-convert tool (i.e. librsvg2-bin Debian package). Needed to compare
  schematics with multiple pages. Converts SVG files to PNGs.
- xdg-open tool (i.e. xdg-utils Debian package). Used to open the PDF viewer.
- [KiAuto](https://github.com/INTI-CMNB/KiAuto/). Used to print the schematic
  in PDF format.

In a Debian/Ubuntu system you'll first need to add this
[repo](https://set-soft.github.io/debian/) and then use:

```shell
$ sudo apt-get install kidiff
```

Arch Linux can install
[kicad-pcb-diff](https://aur.archlinux.org/packages/kidiff) using the AUR
repository:

```bash
$ yay -S kidiff
```

Note: if you are using Debian, or some derived distro like Ubuntu, you can
find a Debian package in the releases section. But using the repo is simpler.

## Standalone use

1. As root run:

```shell
# make install
```

The scripts will be copied to */usr/local/bin*. If you want to install the
scripts in */usr/bin* run

```shell
# make prefix=/usr install
```

Note: if you are using Debian, or some derived distro like Ubuntu, you can
find a Debian package in the releases section.

## Docker image

You can find a docker image containing KiDiff and other KiCad tools
[here](https://github.com/INTI-CMNB/kicad_auto).

## Git plug-in

1. Install the scripts
2. To initialize a repo just run the *kicad_pcb-diff-init.py* script from the
   root of the repo.\
   This will configure the repo to read extra configuration
   from the *.gitconfig* file.\
   It will also associate the *kicad_pcb* file
   extension with the *kicad-git-diff.py* script.
3. The initialization script will create a list of layers to be excluded in
   the *.kicad-git-diff* file.\
   Review this file and adjust it to your needs.
   Lines starting with *#* will be ignored.

Once configured the tool will be used every time you do a diff using *git*.

### Temporarily disabling the git plug-in

Sometimes the graphics diff is not what you want. To disable it just invoke
`git diff` using the `--no-ext-diff` option. It will force the text mode
original diff behavior.

### Disabling the pager

Git will use a pager to allow scrolling back and forth. This could be annoying
because you must exit it, the git option `--no-pager` disables it. Example:

```shell
$ git --no-pager diff XXXXXX.kicad_pcb
```

## PDF conversion policy

On some systems (i.e. Debian) ImageMagick disables PDF manipulation in its
*policy.xml* configuration file. Comment or remove lines like this:

```
<policy domain="coder" rights="none" pattern="PDF" />
```

On Debian 11/12 this applies to the */etc/ImageMagick-6/policy.xml* and/or
*/etc/ImageMagick-7/policy.xml* file.

# Usage

The *kicad-git-diff.py* is a plug-in for *git* so you just need to configure
*git* and then it becomes transparent. If you need to create a diff between
two files outside *git* you can use the *kicad-diff.py* script.

You have to provide the name of the two PCB/SCHs to be compared. The first is
the old one, the reference, and the second is the new, the one you want to
compare. The additional command line options are:

## --help

Shows a detailed list of the available options.

## --all_pages

Compare all pages for a schematic. Note that the tool doesn't currently
support adding or removing sheets, both documents must have the same amount of
pages.

## --cache_dir

The PCB/SCH files are plotted to PDF files. One PDF file for layer. To avoid
plotting them over and over you can specify a cache directory to store the
PDFs.

## --diff_mode

Selects the mechanism used to represent the differences:

- **red_green** this is the default mode. Here we try to mimic the colored
  text mode diff tools. Things added to the *old* file are represented in
  green and things removed in red.
- **stats** in this mode all difference are represented in red. We compute the
  amount of pixels that are different, you can use this value to determine if
  the changes are significant. See the `--fuzz` and `--threshold` options.

## --exclude

Specifies the name of a file containing a list of layers to be excluded. Each
line of the file is interpreted as a layer name. An example for this file
could be:

```raw
B.Adhes
F.Adhes
Cmts.User
Eco1.User
Eco2.User
Edge.Cuts
Margin
```

You can also use the KiCad internal layer ID number. This will avoid warnings
about undefined layer names.

Note that when using the *git* plug-in the script looks for a file named
*.kicad-git-diff* at the root of the repo.

Using this you can reduce the time wasted computing diffs for empty or useless
layers.

Note that lines starting with # are skipped.

See also `--layers`

## --force_gs

KiDiff uses poppler utils if they are available. When they aren't KiDiff can
use Ghostscript. The results using poppler are better and the process is
faster, but you can choose to use Ghostscript using this option.

## --fuzz

When comparing using the *stats* mode (see `--diff_mode`) this option controls
how strict is the color comparison. The default is to tolerate 5 % of error in
the colors. Enlarge it if you want to ignore bigger differences in the colors.

## --keep_pngs

Don't remove the individual PNGs. Complements `--output_dir`. They are usually
removed as soon as we get the output PDF.

## --layers

Specifies the name of a file containing a list of layers to be included. This
option works similar to `--exclude` but we process only the layers indicated
here.

Important: when this list is only composed by layer numbers KiDiff skips any
check and uses this list of layers, even if they aren't defined in any of the
specified PCBs. Otherwise you can get warnings about names not defined.

`--layers` and `--exclude` are mutually exclusive.

## --new_file_hash

This is the equivalent of the *--old_file_hash* option used for the new
PCB/SCH file.

## --no_reader

Use it to avoid invoking the default PDF viewer. Note that you should also
provide an output directory using *--output_dir*.

The default PDF reader is invoked using *xdg-open*

## --old_file_hash

The plotted PDF files for each layer are stored in the cache directory using a
SHA1 of the PCB/SCH file as name for the directory. You can specify another
hash here to identify the old PCB/SCH file.

The *git* plug-in uses the hash provided by *git* instead of the SHA1 for the
file.

## --output_dir

Five seconds after invoking the PDF viewer the output files are removed. If
you want to keep them for later review, or five seconds isn't enough for your
system, you can specify a directory to store the generated files.

Note: individual PNGs are always removed, consult `--keep_pngs`

## --output_name

Used to complement `--output_dir`. The default name is `diff.pdf`

## --resolution

The PDF files are converted to bitmaps to be compared. The default resolution
for these bitmaps is 150 DPIs. This is a compromise between speed and
legibility. For faster compares you can use a smaller resolution. For detailed
comparison you can use a higher resolution. Be careful because the time is
increased exponentially. You can also run out of resources. In particular
ImageMagick defines some limits to the disk used for operations. These limits
can be very low for default installations. You can consult the limits using
the following command:

`identify -list resource`

Consult ImageMagick documentation in order to increase them.

## --threshold

In the *stats* mode this option can make KiDiff to return an error value if
the difference is bigger than the specified threshold. Indicating 0 means that
we don't look for errors, KiDiff always returns 0.

## -v/--verbose

Increases the level of verbosity. The default is a quite mode, specifying one
level (*-v*) you'll get information messages about what's going on. If you
increase the level to two (*-vv*) you'll get very detailed information, most
probably useful only to debug problems.

## --version

Print the script version, copyright and license.

# Advanced use

`kicad-diff.py` can be run using the `--only_cache` option. In this mode the
*new_file* argument can be the same as the *old_file* argument. This operation
is used to store the images, but skip the comparison. In order to work you
must specify a valid `cache_dir`. You should also take note of the hash used
by `kicad-diff.py`, or just provide one using the `--old_file_hash`.

You can then compare two files using the cached images, you just need to
provide the hashes you want to compare. The *old_file* and *new_file* won't be
used.

# Similar tools

## KiCad-Diff

[KiCad-Diff](https://github.com/Gasman2014/KiCad-Diff) is a diff tool for
PCBs, is more oriented to GUI use. It has support not only for `git` but also
for `fossil` and `svn`. You can navigate the diffs and get information about
added or removed items, all using a browser. And is fast (all is handled using
SVGs).

It doesn't support schematics, can't be directly used as a git plug-in
(perhaps using some wrapper), can't measure the ammout of difference and
doesn't generate a file to see the differences (only browsable).

# Credits and notes

- This script is strongly based on Jesse Vincent
  [work](https://github.com/obra/kicad-tools).
- I borrowed the command to compare two images from Brecht Machiels. In
  particular from his
  [diffpdf.sh](https://gist.github.com/brechtm/891de9f72516c1b2cbc1) tool.
- I'm not a Python programmer, stackoverflow helps me ...
