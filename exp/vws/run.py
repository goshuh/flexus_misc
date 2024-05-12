#!/usr/bin/python3

import os

import argparse

from .work import misc


REQPS = [
    20000,
    40000,
    60000,
    80000,
    10000,
    120000,
    140000,
    160000,
    180000
]

CHAIN = [
    256,
    64,
    16,
    4,
    1
]


def parse_args():
    args = argparse.ArgumentParser(description = 'run')

    args.add_argument('-s', type = misc.pow2, default = 1)
    args.add_argument('-w', type = misc.pow2, default = 8192)
    args.add_argument('-i', type = misc.pow2, default = 32768)
    args.add_argument('-j', type = misc.pow2, default = 2097152)

    return args.parse_known_args()[0]


def run(trans, work):
    args = parse_args()
    core = os.cpu_count()

    #
    snap = []

    for r in REQPS:
        for c in CHAIN:
            snap.append((f'{work}_{trans}_{r}_{c}', '', f'/bin/{work} -t {trans} -r {r} -c {c}'))

    misc.para('running snap', core, misc.snap, snap)

    #
    sets = args.j // (64 * 16)

    cfgs = (
        ' '.join(map(str, [
            '-mmu:dvlbsets', args.s,
            '-mmu:dvlbways', args.w,
            '-mmu:vlbtest', 'true',
            '-L1d:size', args.i,
            '-L2:size', args.j,
            '-L2:directory_type', f'Standard:sets={sets}:assoc=16:repl=lru',
        ])),
        ' '.join(map(str, [
            '-mmu:dvlbsets', args.s,
            '-mmu:dvlbways', args.w,
            '-mmu:vlbtest', 'true',
            '-L1d:array_config', f'STD:size={args.i}:assoc=8:repl=lru',
            '-L2:array_config', f'STD:total_sets={sets}:assoc=16:repl=lru',
            '-L2:dir_config', f'sets={sets}:assoc=16'
        ]))
    )

    flex = []

    for r in REQPS:
        for c in CHAIN:
            flex.append((f'{work}_{trans}_{r}_{c}', cfgs))

    tag = f'{misc.kmgt(args.s)}-{misc.kmgt(args.w)}_{misc.kmgt(args.i)}_{misc.kmgt(args.j)}'

    misc.para(f'running {tag}', core, misc.comb, flex)

    dst = misc.prep(os.path.join('results', tag))

    for r in REQPS:
        for c in CHAIN:
            src = f'{work}_{trans}_{r}_{c}'
            misc.copy(src, os.path.join(dst, src))
