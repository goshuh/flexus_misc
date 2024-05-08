#!/usr/bin/python3

import os

import shutil
import subprocess


def prep(src):
    os.makedirs(src, exist_ok = True)

    return src


def copy(src, dst):
    shutil.move(os.path.join(src, 'adv'),               dst)
    shutil.move(os.path.join(src, 'trace.log'),         dst)
    shutil.move(os.path.join(src, 'trace.bin'),         dst)
    shutil.move(os.path.join(src, 'stats_db.out.gz'),   os.path.join(dst, 'trace.gz'))
    shutil.move(os.path.join(src, 'configuration.out'), os.path.join(dst, 'timing.cfg'))

    shutil.move(os.path.join(dsc, 'stats_db.out.gz'),   os.path.join(dst, 'timing.gz'))
    shutil.move(os.path.join(dsc, 'configuration.out'), os.path.join(dst, 'timing.cfg'))


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
        check = True,
        env = {
            'PATH': os.environ['PATH'],
            'HOME': os.environ['HOME'],
            'FLEXUS_CFG_OVERRIDE': ' '.join(list(map(str, cmds)))
        }
    )
