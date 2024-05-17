#!/usr/bin/python3

import os

import argparse

import misc


REQPS = [
    20000,
    40000,
    60000,
    80000,
    100000,
    120000,
    140000,
    160000
]

CHAIN = [
    64,
    32,
    16,
    8,
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

    args.add_argument('-a', default = '-')

    return args.parse_known_args()[0]


def main(t, work):
    args = parse_args()
    core = os.cpu_count()
    step = misc.step(args.a)

    if step(0):
        snap = []
        sdep = []

        rarr = [args.r] if args.r else REQPS
        carr = [args.c] if args.c else CHAIN

        for r in rarr:
            for c in carr:
                path = f'{work}_{t}_{r}_{c}'

                snap.append((path, '', f'/bin/{work} -t {t} -r {r} -c {c}'))
                sdep.append({})

        misc.para('snap', core, misc.snap, snap, sdep)

    flex = []
    fdep = []
    sets = args.j // (64 * 16)

    if step(1):
        farg  = ' '.join(map(str, [
            '-mmu:dvlbsets',        args.s,
            '-mmu:dvlbways',        args.w,
            '-mmu:vlbtest',        'true',
            '-L1d:size',            args.i,
            '-L2:size',             args.j,
            '-L2:directory_type', f'Standard:sets={sets}:assoc=16:repl=lru',
        ]))

        for r in rarr:
            for c in carr:
                path = f'{work}_{t}_{r}_{c}'

                flex.append((path, 'trace',  farg))
                fdep.append({})

    if step(2):
        flen = len(fdep)

        targ = ' '.join(map(str, [
            '-mmu:dvlbsets',        args.s,
            '-mmu:dvlbways',        args.w,
            '-mmu:vlbtest',        'true',
            '-L1d:array_config',  f'STD:size={args.i}:assoc=8:repl=lru',
            '-L2:array_config',   f'STD:total_sets={sets}:assoc=16:repl=lru',
            '-L2:dir_config',     f'sets={sets}:assoc=16'
        ]))

        for r in rarr:
            for c in carr:
                path = f'{work}_{t}_{r}_{c}'

                flex.append((path, 'timing', targ))
                fdep.append({len(fdep) - flen} if flex else {})

    conf = f'{misc.kmgt(args.s)}-{misc.kmgt(args.w)}_{misc.kmgt(args.i)}_{misc.kmgt(args.j)}'

    if step(2, 3):
        misc.para(conf, core, misc.flex, flex, fdep)

    if step(3):
        dest = misc.prep(os.path.join('res', conf))

        for r in REQPS:
            for c in CHAIN:
                path = f'{work}_{t}_{r}_{c}'

                misc.copy(path, os.path.join(dest, path))
