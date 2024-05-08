#!/usr/bin/python3

import os

import time
import shutil
import multiprocessing

from . import runq


def prep(src):
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
            pool.apply(func, args = a)

        pool.close()
        pool.join()


def snap(snap, rarg = '', warg = ''):
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

    os.environ['FLEXUS_LOG_OVERRIDE'] = f'{mode}.log'
    os.environ['FLEXUS_CFG_OVERRIDE'] = cfgs

    runq.runq({
         mode:  '1',
        'wait': '1',
        'snap': snap,
        'stdout': f'{snap}/{mode}.out',
        'stderr': '-'
    })


def comb(snap, cfgs):
    flex('trace',  snap, cfgs)
    flex('timing', snap, cfgs)
