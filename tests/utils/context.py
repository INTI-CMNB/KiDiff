import os
import shutil
import tempfile
import logging
import subprocess
import re
import configparser
from glob import glob
from pty import spawn
from contextlib import contextmanager
from psutil import pid_exists
import sys
# Look for the 'kiauto' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(script_dir)))
from kiauto.ui_automation import recorded_xvfb, PopenContext

COVERAGE_SCRIPT = 'python3-coverage'
KICAD_PCB_EXT = '.kicad_pcb'
MODE_SCH = 1
MODE_PCB = 0

ng_ver = os.environ.get('KIAUS_USE_NIGHTLY')
if ng_ver:
    # Path to the Python module
    sys.path.insert(0, '/usr/lib/kicad-nightly/lib/python3/dist-packages')
import pcbnew
# Detect version
m = re.match(r'(\d+)\.(\d+)\.(\d+)', pcbnew.GetBuildVersion())
major = int(m.group(1))
minor = int(m.group(2))
patch = int(m.group(3))
kicad_version = major*1000000+minor*1000+patch
logging.debug('Detected KiCad v{}.{}.{} ({})'.format(major, minor, patch, kicad_version))
ki5 = kicad_version < 5099000
ki6 = not ki5


def usable_cmd(cmd):
    return ' '.join(cmd)


def get_config_vars_ini(file):
    if not os.path.isfile(file):
        return None
    config = configparser.ConfigParser()
    with open(file, "rt") as f:
        data = f.read()
    config.read_string('[Various]\n'+data)
    if 'EnvironmentVariables' in config:
        return config['EnvironmentVariables']
    return None


class TestContext(object):
    pty_data = None

    def __init__(self, test_dir, case_num, test_name=None, mode=MODE_PCB):
        if test_name is None:
            test_name = sys._getframe(1).f_code.co_name
        if test_name.startswith('test_'):
            test_name = test_name[5:]
        self.board_dir = os.path.join('..', 'cases')
        if ki5:
            self.kicad_cfg_dir = pcbnew.GetKicadConfigPath()
            self.kicad_conf = os.path.join(self.kicad_cfg_dir, 'kicad_common')
            env = get_config_vars_ini(self.kicad_conf)
            if env and 'kicad_config_home' in env:
                self.kicad_cfg_dir = env['kicad_config_home']
            self.sch_ext = '.sch'
            self.pro_ext = '.pro'
            self.pcbnew_conf = os.path.join(self.kicad_cfg_dir, 'pcbnew')
            self.eeschema_conf = os.path.join(self.kicad_cfg_dir, 'eeschema')
        else:
            # self.kicad_cfg_dir = pcbnew.SETTINGS_MANAGER.GetUserSettingsPath().replace('/kicad/', '/kicadnightly/')
            self.kicad_cfg_dir = pcbnew.SETTINGS_MANAGER.GetUserSettingsPath()
            self.sch_ext = '.kicad_sch'
            self.pro_ext = '.kicad_pro'
            self.pcbnew_conf = os.path.join(self.kicad_cfg_dir, 'pcbnew.json')
            self.eeschema_conf = os.path.join(self.kicad_cfg_dir, 'eeschema.json')
            self.kicad_conf = os.path.join(self.kicad_cfg_dir, 'kicad_common.json')
        # We are using PCBs
        self.mode = mode
        self.kind = 'Schematic' if mode == MODE_SCH else 'PCB'
        # The name used for the test output dirs and other logging
        self.test_name = test_name
        # The name of the PCB board file
        self.case_num = str(case_num)
        # The actual board file that will be loaded
        self._get_work_file_name()
        # The actual output dir for this run
        self._set_up_output_dir(test_dir)
        # stdout and stderr from the run
        self.out = None
        self.err = None
        self.proc = None
        # Where is the reference output for this test
        self.set_ref_dir()
        self.include_lst = 'include.lst'

    def set_ref_dir(self, extra=''):
        self.ref_dir = os.path.join('tests', 'cases', str(self.case_num),
                                    'ref_'+('pcb' if self.mode == MODE_PCB else 'sch')+extra)

    def _get_work_files_dir(self):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.abspath(os.path.join(this_dir, self.board_dir))

    def _get_work_file_name_x(self, x):
        return os.path.join(self._get_work_files_dir(), self.case_num, x, self.case_num +
                            (KICAD_PCB_EXT if self.mode == MODE_PCB else self.sch_ext))

    def _get_work_file_name(self):
        self.work_file_a = self._get_work_file_name_x('a')
        self.work_file_b = self._get_work_file_name_x('b')
        logging.info('{} files: {} / {}'.format(self.kind, self.work_file_a, self.work_file_b))
        assert os.path.isfile(self.work_file_a), self.work_file_a
        assert os.path.isfile(self.work_file_b), self.work_file_b

    def invert(self):
        """ Do the diff in the reverse order """
        aux = self.work_file_a
        self.work_file_a = self.work_file_b
        self.work_file_b = aux

    def _set_up_output_dir(self, test_dir):
        self.output_dir = os.path.join(test_dir, self.test_name)
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info('Output dir: '+self.output_dir)

    def clean_up(self):
        logging.debug('Clean-up')

    def get_out_path(self, filename):
        return os.path.join(self.output_dir, filename)

    def expect_out_file(self, filename):
        file = self.get_out_path(filename)
        assert os.path.isfile(file)
        assert os.path.getsize(file) > 0
        return file

    def dont_expect_out_file(self, filename):
        file = self.get_out_path(filename)
        assert not os.path.isfile(file)

    def create_dummy_out_file(self, filename):
        file = self.get_out_path(filename)
        with open(file, 'w') as f:
            f.write('Dummy file\n')

    def get_pro_filename(self):
        return os.path.join(self._get_work_files_dir(), self.case_num, self.case_num+self.pro_ext)

    def get_prl_filename(self):
        return os.path.join(self._get_work_files_dir(), self.case_num, self.case_num+'.kicad_prl')

    def get_prodir_filename(self, file):
        return os.path.join(self._get_work_files_dir(), self.case_num, file)

    def get_pro_mtime(self):
        return os.path.getmtime(self.get_pro_filename())

    def get_prl_mtime(self):
        if ki5:
            return os.path.getmtime(self.get_pro_filename())
        return os.path.getmtime(self.get_prl_filename())

    def get_sub_sheet_name(self, sub, ext):
        if ki5:
            return sub.lower()+'-'+sub+'.'+ext
        return self.case_num+'-'+sub+'.'+ext

    @staticmethod
    def read(fd):
        data = os.read(fd, 1024)
        TestContext.pty_data += data
        return data

    def run(self, ops=None, ret_val=None, extra=None, use_a_tty=False, filename=None, ignore_ret=False, no_dir=False,
            layers=False):
        logging.debug('Running '+self.test_name)
        # Change the command to be local and add the board and output arguments
        cmd = [COVERAGE_SCRIPT, 'run', '-a']
        cmd += ['kicad-diff.py', '-vvv', '--cache', 'cache', '--output_dir', self.output_dir, '--no_reader', '--keep_pngs']
        if layers:
            cmd += ['--layers', os.path.join(self._get_work_files_dir(), self.case_num, self.include_lst)]
        if ops:
            cmd += ops
        cmd += [self.work_file_a, self.work_file_b]
        logging.debug(usable_cmd(cmd))

        out_filename = self.get_out_path('output.txt')
        err_filename = self.get_out_path('error.txt')
        exp_ret = 0 if ret_val is None else ret_val

        retry = 2
        while retry:
            if use_a_tty:
                # This is used to test the coloured logs, we need stderr to be a TTY
                TestContext.pty_data = b''
                ret_code = spawn(cmd, self.read)
                self.err = TestContext.pty_data.decode()
                self.out = self.err
            else:
                # Redirect stdout and stderr to files
                f_out = os.open(out_filename, os.O_RDWR | os.O_CREAT)
                f_err = os.open(err_filename, os.O_RDWR | os.O_CREAT)
                # Run the process
                process = subprocess.Popen(cmd, stdout=f_out, stderr=f_err)
                ret_code = process.wait()
            logging.debug('ret_code '+str(ret_code))
            if not ((ret_code == 9 or ret_code == 10) and exp_ret != 9 and exp_ret != 10):
                break
            retry -= 1
            if retry:
                logging.debug('Retrying ...')
                os.rename(self.output_dir, self.output_dir+'_RETRY_'+str(retry))
                os.makedirs(self.output_dir, exist_ok=True)
        if not ignore_ret:
            assert ret_code == exp_ret, "got {} when {} expected".format(ret_code, exp_ret)
        if use_a_tty:
            with open(out_filename, 'w') as f:
                f.write(self.out)
            with open(err_filename, 'w') as f:
                f.write(self.out)
        else:
            # Read stdout
            os.lseek(f_out, 0, os.SEEK_SET)
            self.out = os.read(f_out, 1000000)
            os.close(f_out)
            self.out = self.out.decode()
            # Read stderr
            os.lseek(f_err, 0, os.SEEK_SET)
            self.err = os.read(f_err, 1000000)
            os.close(f_err)
            self.err = self.err.decode()

    def search_out(self, text):
        m = re.search(text, self.out, re.MULTILINE)
        return m

    def search_err(self, text):
        m = re.search(text, self.err, re.MULTILINE)
        return m

    def search_in_file(self, file, texts):
        logging.debug('Searching in "'+file+'" output')
        with open(self.get_out_path(file)) as f:
            txt = f.read()
        for t in texts:
            logging.debug('- r"'+t+'"')
            m = re.search(t, txt, re.MULTILINE)
            assert m

    @staticmethod
    def cmd_compare(img, ref, diff, fuzz):
        return ['compare',
                # Tolerate 30/50 % error in color
                '-fuzz', fuzz,
                # Count how many pixels differ
                '-metric', 'AE',
                # Create a 720p image
                '-size', 'x720',
                img, ref,
                # Avoid the part where KiCad version and title are printed
                # Also avoid the upper numbers. KiCad 5.1.7 changed the place for "1"
                # '-crop', '100%x80%+0+36',
                # Remove the area outside the image
                '+repage',
                '-colorspace', 'RGB',
                diff]

    @staticmethod
    def _compare_image(img, ref, diff, fuzz='30%'):
        exact = int(fuzz[:-1]) <= 30
        cmd = TestContext.cmd_compare(img, ref, diff, fuzz)
        logging.debug('Comparing images with: '+usable_cmd(cmd))
        res = subprocess.run(cmd, stderr=subprocess.PIPE)
        assert res.returncode == 0 or not exact, "Compare failed for {} vs {}".format(ref, img)
        # m = re.match(r'([\d\.e-]+) \(([\d\.e-]+)\)', res.decode())
        # assert m
        # logging.debug('MSE={} ({})'.format(m.group(1), m.group(2)))
        ae = int(res.stderr.decode())
        logging.debug('AE=%d' % ae)
        assert ae == 0 if exact else ae < 100, ae

    def compare_image(self, image, reference=None, diff='diff.png', fuzz='30%'):
        """ For images and single page PDFs """
        if reference is None:
            reference = image
        self._compare_image(self.get_out_path(image), os.path.join(self.ref_dir, reference), self.get_out_path(diff), fuzz)

    def svg_to_png(self, svg):
        png = os.path.splitext(svg)[0]+'.png'
        logging.debug('Converting '+svg+' to '+png)
        # cmd = ['convert', '-density', '150', svg, png]
        cmd = ['rsvg-convert', '-d', '150', '-p', '150', '-o', png, svg]
        subprocess.check_call(cmd)
        return os.path.basename(png)

    def compare_svg(self, image, reference=None, diff='diff.png'):
        """ For SVGs, rendering to PNG """
        if reference is None:
            reference = image
        image_png = self.svg_to_png(self.get_out_path(image))
        reference_png = self.svg_to_png(os.path.join(self.ref_dir, reference))
        self.compare_image(image_png, reference_png, diff)
        os.remove(os.path.join(self.ref_dir, reference_png))

    def ps_to_png(self, ps):
        png = os.path.splitext(ps)[0]+'.png'
        logging.debug('Converting '+ps+' to '+png)
        cmd = ['convert', '-density', '150', ps, '-rotate', '90', png]
        subprocess.check_call(cmd)
        return os.path.basename(png)

    def compare_ps(self, image, reference=None, diff='diff.png'):
        """ For PSs, rendering to PNG """
        if reference is None:
            reference = image
        image_png = self.ps_to_png(self.get_out_path(image))
        reference_png = self.ps_to_png(os.path.join(self.ref_dir, reference))
        self.compare_image(image_png, reference_png, diff)
        os.remove(os.path.join(self.ref_dir, reference_png))

    def compare_out_file(self, out_file='diff.pdf'):
        self.compare_pdf(out_file)

    def compare_out_pngs(self, out_file='diff.pdf'):
        out_file = os.path.splitext(out_file)[0]
        refs = os.path.join(self.ref_dir, out_file+'-*.png')
        pngs = glob(refs)
        assert pngs, "Nothing at "+refs
        for png in pngs:
            name = os.path.basename(png)
            diff = os.path.splitext(name)[0]+'-diff.png'
            self.compare_image(name, name, diff=diff)

    def compare_pdf(self, gen, reference=None, diff='diff-{}.png'):
        """ For multi-page PDFs """
        if reference is None:
            reference = gen
        logging.debug('Comparing PDFs: '+gen+' vs '+reference+' (reference)')
        # Split the reference
        logging.debug('Splitting '+reference)
        cmd = ['convert', '-density', '150',
               os.path.join(self.ref_dir, reference),
               self.get_out_path('ref-%d.png')]
        subprocess.check_call(cmd)
        # Split the generated
        logging.debug('Splitting '+gen)
        cmd = ['convert', '-density', '150',
               self.get_out_path(gen),
               self.get_out_path('gen-%d.png')]
        subprocess.check_call(cmd)
        # Chek number of pages
        ref_pages = glob(self.get_out_path('ref-*.png'))
        gen_pages = glob(self.get_out_path('gen-*.png'))
        logging.debug('Pages {} vs {}'.format(len(gen_pages), len(ref_pages)))
        assert len(ref_pages) == len(gen_pages)
        # Compare each page
        for page in range(len(ref_pages)):
            self._compare_image(self.get_out_path('ref-'+str(page)+'.png'),
                                self.get_out_path('gen-'+str(page)+'.png'),
                                self.get_out_path(diff.format(page)))

    def compare_txt(self, text, reference=None, diff='diff.txt'):
        if reference is None:
            reference = text
        cmd = ['/bin/sh', '-c', 'diff -ub '+os.path.join(self.ref_dir, reference)+' ' +
               self.get_out_path(text)+' > '+self.get_out_path(diff)]
        logging.debug('Comparing texts with: '+usable_cmd(cmd))
        res = subprocess.call(cmd)
        assert res == 0

    def filter_txt(self, file, pattern, repl):
        fname = self.get_out_path(file)
        with open(fname) as f:
            txt = f.read()
        with open(fname, 'w') as f:
            f.write(re.sub(pattern, repl, txt))

    @contextmanager
    def start_kicad(self, cmd, cfg):
        """ Context manager to run a command under a virual X server.
            Use like this: with context.start_kicad('command'): """
        with recorded_xvfb(cfg):
            if isinstance(cmd, str):
                cmd = [cmd]
            with PopenContext(cmd, stderr=subprocess.DEVNULL, close_fds=True) as self.proc:
                logging.debug('Started `'+str(cmd)+'` with PID: '+str(self.proc.pid))
                assert pid_exists(self.proc.pid)
                yield
                logging.debug('Ending KiCad context')

    def stop_kicad(self):
        if self.proc:
            logging.debug('Stopping KiCad')
            assert pid_exists(self.proc.pid)
            self.proc.terminate()
            self.proc = None


class TestContextSCH(TestContext):

    def __init__(self, test_dir, case_num, test_name=None, old_sch=False):
        if test_name is None:
            test_name = sys._getframe(1).f_code.co_name
        if test_name.startswith('test_'):
            test_name = test_name[5:]
        super().__init__(test_dir, case_num, test_name, mode=MODE_SCH)
        if old_sch:
            self.sch_ext = '.sch'
        self._get_work_file_name()
