#!/usr/bin/python3

import os

import importlib


ASSOC = [
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
    '01',
    '02',
    '04',
    '08',
    '16',
    '32'
]


def run(work):
    misc = importlib.import_module('.work.misc', package = __package__)

    with open('snap.cmd', 'w') as snap, open('flex.cmd', 'w') as flex:
        for r in REQPS:
            for c in CHAIN:
                src = f'{work}_{r}_{c}'

                snap.write(f'WORK_ARGS="{work} -r {r} -c {c}" ./snap {src}\n')

                flex.write(f'./flex trace {src} && ./flex timing {src}\n')

    core = os.cpu_count() - 2

    misc.para('snap.cmd', 'running snap', core)

    for a in ASSOC:
        misc.para('flex.cmd', f'running {a}', core,
            '-mmu:dvlbsets', '1',
            '-mmu:dvlbways', a,
            '-mmu:vlbtest', 'true'
        )

        dst = misc.prep(os.path.join('results', a))

        for r in REQPS:
            for c in CHAIN:
                src = f'{work}_{r}_{c}'

                misc.copy(src, misc.prep(os.path.join(dst, src)))
