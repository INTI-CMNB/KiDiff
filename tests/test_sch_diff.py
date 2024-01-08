# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnologïa Industrial
# License: GPL-2.0
# Project: KiCad Diff (KiDiff)
"""
Tests for PCB diffs

For debug information use:
pytest-3 --log-cli-level debug --test_dir=pp -k TEST

"""

import os
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context


def test_sch_simple_1(test_dir):
    ctx = context.TestContextSCH(test_dir, 1)
    ctx.run()
    ctx.compare_out_pngs()
    ctx.clean_up()


def test_sch_multi_1(test_dir):
    ctx = context.TestContextSCH(test_dir, 2)
    ctx.run(['--all_pages'])
    ctx.compare_out_file()
    ctx.clean_up()


def test_sch_diff_sheets_1(test_dir):
    ctx = context.TestContextSCH(test_dir, 5)
    ctx.run(['--all_pages'])
    ctx.compare_out_pngs()
    ctx.invert()
    ctx.set_ref_dir(extra='2')
    ctx.run(['--all_pages'])
    ctx.compare_out_pngs()
    ctx.clean_up()


def test_sch_diff_size_1(test_dir):
    ctx = context.TestContextSCH(test_dir, 6)
    ctx.run()
    ctx.compare_out_pngs()
    ctx.clean_up()
