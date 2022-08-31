# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnologïa Industrial
# License: GPL-2.0
# Project: KiCad Diff (KiDiff)
"""
Tests for PCB diffs

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context


def test_pcb_simple_1(test_dir):
    ctx = context.TestContext(test_dir, 1)
    ctx.run()
    ctx.compare_out_pngs()
    ctx.clean_up()


def test_pcb_diff_layers_1(test_dir):
    ctx = context.TestContext(test_dir, 4)
    ctx.run(layers=True)
    ctx.compare_out_pngs()
    ctx.invert()
    ctx.set_ref_dir(extra='2')
    ctx.run(layers=True)
    ctx.compare_out_pngs()
    ctx.clean_up()


def test_pcb_diff_layers_2(test_dir):
    """ Using names instead of numbers in the include.lst """
    ctx = context.TestContext(test_dir, 4)
    ctx.include_lst = 'include_names.lst'
    ctx.run(layers=True)
    ctx.compare_out_pngs()
    ctx.clean_up()
