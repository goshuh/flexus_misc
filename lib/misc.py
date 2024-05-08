#!/usr/bin/python3

import os

import shutil
import subprocess


def prep(src):
    os.makedirs(src, exist_ok = True)

    return src


def copy(src, dst):
    def move(src, dst):
        try:
            shutil.move(src, dst)
        except:
            pass

    move(os.path.join(src, 'adv'),                      dst)
    move(os.path.join(src, 'trace.log'),                dst)
    move(os.path.join(src, 'trace.bin'),                dst)
    move(os.path.join(src, 'stats_db.out.gz'),          os.path.join(dst, 'trace.gz'))
    move(os.path.join(src, 'configuration.out'),        os.path.join(dst, 'trace.cfg'))

    move(os.path.join(dst, 'adv', 'stats_db.out.gz'),   os.path.join(dst, 'timing.gz'))
    move(os.path.join(dst, 'adv', 'configuration.out'), os.path.join(dst, 'timing.cfg'))


def para(file, info, core, *cmds):
    print(info)

    subprocess.run([
        'parallel',
            '--env', 'FLEXUS_CFG_OVERRIDE',
            '--arg-file', file,
            '--max-lines', '1',
            '--max-procs', str(core)
        ],
        shell = False,
        check = False,
        env = {
            'PATH': os.environ['PATH'],
            'HOME': os.environ['HOME'],
            'FLEXUS_CFG_OVERRIDE': ' '.join(list(map(str, cmds)))
        }
    )
