#!/usr/bin/python3

import os
import sys

import time
import shutil
import signal

import runq


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

    if mul == 1:
        return int(src)
    else:
        return int(src[:-1]) * mul


def kmgt(src):
    pow = 0
    fix = ['', 'k', 'm', 'g', 't']

    while src >= 1024:
        src = src // 1024
        pow = pow +  1

    return f'{src}{fix[pow]}'


def step(src):
    class comp(object):
        def __init__(self, pre, suf):
            self.pre = int(pre)
            self.suf = int(suf)

        def __call__(self, *arr):
            for a in arr:
                if self.pre <= a <= self.suf:
                    return True
            return False

    src = src.split(':')

    pre = src[0] if len(src) > 0 else '-'
    suf = src[1] if len(src) > 1 else pre

    if pre == '-':
        pre = '0'
    if suf == '-':
        suf = '100'

    return comp(pre, suf)


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


def para(info, core, func, args, deps):
    print(info)

    # the multiprocessing.Pool sucks
    pids = {}
    curr = []
    rmap = [[] for _ in range(len(args))]

    def wipe(sig, frame):
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except:
                pass

        os._exit(1)

    signal.signal(signal.SIGINT,  wipe)
    signal.signal(signal.SIGTERM, wipe)

    def wait():
        i = pids.pop(os.waitpid(-1, 0)[0])

        for r in rmap[i]:
            deps[r].remove(i)

            if not deps[r]:
                curr.append((r, args[r]))

    for i, dep in enumerate(deps):
        if isinstance(dep, (int, list)):
            dep = deps[i] = set(i)

        for d in dep:
            rmap[d].append(i)

    for i, (arg, dep) in enumerate(zip(args, deps)):
        if not dep:
            curr.append((i, arg))

    while curr:
        while curr:
            if len(pids) == core:
                wait()

            i, arg = curr.pop()

            if not (pid := os.fork()):
                while True:
                    try:
                        print(f'  {func.__name__}({", ".join(arg)})')
                        break
                    except BlockingIOError:
                        pass

                func(*arg)
                os._exit(0)

            pids[pid] = i

        while pids:
            wait()

            if curr:
                break


def snap(snap, rarg = '', warg = ''):
    if os.path.isfile(os.path.join(snap, 'vmstate')):
        return

    prep(snap)

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


def flex(pref, snap, mode, cfgs):
    orig = snap
    snap = os.path.join(pref, snap)

    if mode == 'timing':
        snap = os.path.join(snap, 'adv')

        if not os.path.isfile(snap, 'vmstate'):
            sys.exit(f'ERROR: {snap} does not exist')

    else:
        olds = os.path.join(orig, 'vmstate')
        news = os.path.join(snap, 'vmstate')

        if not os.path.isfile(olds):
            sys.exit(f'ERROR: {olds} does not exist')

        prep(snap)

        if not os.path.islink(news):
            os.symlink(os.path.abspath(olds), news)

    os.environ['FLEXUS_LOG_OVERRIDE'] = f'{mode}.log'
    os.environ['FLEXUS_CFG_OVERRIDE'] = cfgs

    runq.runq({
         mode: snap,
        'stdout': f'{snap}/{mode}.out',
        'stderr':  '-'
    })
