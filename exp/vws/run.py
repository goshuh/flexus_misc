#!/usr/bin/python3

import os

import importlib


ASSOC = [
    '8192',
    '4096',
    '2048',
    '1024',
    '512',
    '256',
    '128',
    '64',
    '32',
    '16',
    '8'
]

REQPS = [
    '40000',
    '80000',
    '120000',
    '160000',
    '200000',
    '240000',
    '280000'
]

CHAIN = [
    '32',
    '16',
    '08',
    '04',
    '02',
    '01'
]


def run(work):
    misc = importlib.import_module('.work.misc', package = __package__)
    core = os.cpu_count() - 2

    #
    snap = []

    for r in REQPS:
        for c in CHAIN:
            snap.append((f'{work}_{r}_{c}', '', f'/bin/{work} -r {r} -c {c}'))

    misc.para('running snap', core, misc.snap, snap)

    #
    for a in ASSOC:
        cfgs = ' '.join([
            '-mmu:dvlbsets', '1',
            '-mmu:dvlbways', a,
            '-mmu:vlbtest', 'true'
        ])

        flex = []

        for r in REQPS:
            for c in CHAIN:
                flex.append((f'{work}_{r}_{c}', cfgs))

        misc.para(f'running {a}', core, misc.comb, flex)

        dst = misc.prep(os.path.join('results', a))

        for r in REQPS:
            for c in CHAIN:
                src = f'{work}_{r}_{c}'
                misc.copy(src, os.path.join(dst, src))