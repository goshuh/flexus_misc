#!/usr/bin/python3

import os

import time
import shutil
import multiprocessing

from . import runq


def pow2(src):
    src = src.replace(' ', '')
    mul = 1

    match src[-1]:
        case 'k' | 'K':
            mul = 1024
        case 'm' | 'M':
            mul = 1024 ** 2
        case 'g' | 'G':
            mul = 1024 ** 3
        case 't' | 'T':
            mul = 1024 ** 4

    return int(src[:-1]) * mul


def kmgt(src):
    pow = 0
    fix = ['', 'k', 'm', 'g', 't']

    while src >= 1024:
        src = src // 1024
        pow = pow +  1

    return f'{src}{fix[pow]}'


def prep(src):
    if os.path.exists(src):
        shutil.rmtree(src)

    os.makedirs(src, exist_ok = True)

    return src


def copy(src, dst):
    def move(src, dst):
        try:
            shutil.move(src, dst)
        except:
            pass

    move(os.path.join(src, 'adv'), dst)

    move(os.path.join(src, 'trace.bin'), dst)
    move(os.path.join(src, 'trace.log'), dst)
    move(os.path.join(src, 'trace.out'), dst)

    move(os.path.join(src, 'stats_db.out.gz'),
         os.path.join(dst, 'trace.gz'))
    move(os.path.join(src, 'configuration.out'),
         os.path.join(dst, 'trace.cfg'))

    move(os.path.join(dst, 'stats_db.out.gz'),
         os.path.join(dst, 'timing.gz'))
    move(os.path.join(dst, 'configuration.out'),
         os.path.join(dst, 'timing.cfg'))


def para(info, core, func, args):
    print(info)

    with multiprocessing.Pool(processes = core) as pool:
        for a in args:
            pool.apply_async(func, args = a)

        pool.close()
        pool.join()


def snap(snap, rarg = '', warg = ''):
    if os.path.isfile(os.path.join(snap, 'vmstate')):
        return

    os.makedirs(snap, exist_ok = True)

    with open(os.path.join(snap, 'snap.cfg'), 'w') as fd:
        if rarg:
            print(f'rarg: {rarg}', file = fd)
        if warg:
            print(f'warg: {warg}', file = fd)

    expt = runq.runq({
        'expect': '1',
        'logfile': os.path.join(snap, 'snap.log')
    }, *rarg.split())

    expt.expect_exact('/ # ')
    expt.sendline(warg)

    expt.expect_exact('INIT_DONE!!!')
    time.sleep(300)

    # ctrl-a
    expt.send('\001')
    expt.send('c')

    expt.expect_exact('(qemu) ')
    expt.sendline('stop')

    expt.expect_exact('(qemu) ')
    expt.sendline(f'savevm-external {snap}')

    expt.expect_exact('(qemu) ')
    expt.sendline('q')


def flex(mode, snap, cfgs):
    if mode == 'timing':
        snap = os.path.join(snap, 'adv')
    elif os.path.isfile(os.path.join(snap, 'adv', 'vmstate')):
        return

    os.environ['FLEXUS_LOG_OVERRIDE'] = f'{mode}.log'
    os.environ['FLEXUS_CFG_OVERRIDE'] = cfgs

    runq.runq({
         mode: snap,
        'wait': '1',
        'stdout': f'{snap}/{mode}.out',
        'stderr': '-'
    })


def comb(snap, cfgs):
    flex('trace',  snap, cfgs[0])
    flex('timing', snap, cfgs[1])
