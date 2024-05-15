#!/usr/bin/python3

import os

import argparse

from .work import misc


REQPS = [
    20000,
    40000,
    60000,
#   80000,
#   120000,
#   160000,
#   200000
]

CHAIN = [
#   256,
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

    args.add_argument('-r', type = int, required = False)
    args.add_argument('-c', type = int, required = False)
    args.add_argument('-q', type = int, default  = 3)

    return args.parse_known_args()[0]


def run(t, work):
    args = parse_args()
    core = os.cpu_count()

    #
    snap = []
    sdep = []

    rarr = [args.r] if args.r else REQPS
    carr = [args.c] if args.c else CHAIN

    for r in rarr:
        for c in carr:
            snap.append((f'{work}_{t}_{r}_{c}', '', f'/bin/{work} -t {t} -r {r} -c {c}'))
            sdep.append({})

    misc.para('running snap', core, misc.snap, snap, sdep)

    if args.q <= 1:
        return

    #
    sets = args.j // (64 * 16)

    farg  = ' '.join(map(str, [
        '-mmu:dvlbsets',        args.s,
        '-mmu:dvlbways',        args.w,
        '-mmu:vlbtest',        'true',
        '-L1d:size',            args.i,
        '-L2:size',             args.j,
        '-L2:directory_type', f'Standard:sets={sets}:assoc=16:repl=lru',
    ]))
    targ = ' '.join(map(str, [
        '-mmu:dvlbsets',        args.s,
        '-mmu:dvlbways',        args.w,
        '-mmu:vlbtest',        'true',
        '-L1d:array_config',  f'STD:size={args.i}:assoc=8:repl=lru',
        '-L2:array_config',   f'STD:total_sets={sets}:assoc=16:repl=lru',
        '-L2:dir_config',     f'sets={sets}:assoc=16'
    ]))

    flex = []
    fdep = []

    for r in rarr:
        for c in carr:
            if args.q >= 2:
                flex.append((f'{work}_{t}_{r}_{c}', 'trace',  farg))
                fdep.append({})

            if args.q >= 3:
                flex.append((f'{work}_{t}_{r}_{c}', 'timing', targ))
                fdep.append({len(fdep) - 1})

    tag = f'{misc.kmgt(args.s)}-{misc.kmgt(args.w)}_{misc.kmgt(args.i)}_{misc.kmgt(args.j)}'

    misc.para(f'running {tag}', core, misc.flex, flex, fdep)

    dst = misc.prep(os.path.join('results', tag))

    for r in REQPS:
        for c in CHAIN:
            src = f'{work}_{t}_{r}_{c}'
            misc.copy(src, os.path.join(dst, src))
