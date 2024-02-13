# Preparation

## Install packages

The following packages should be installed to build QEMU and FLEXUS

- gcc (or g++ in Debian, with C++14 support)
- cmake
- meson
- ninja (maybe as a dependency of meson)
- boost
- glib (may also be called glib-2.0)

No requirements for old/outdated Linux distributions. Just use latest ones.

## Clone repositories

```sh
git clone -b qflex https://github.com/goshuh/midgard_qemu
git clone https://github.com/goshuh/flexus
git clone https://github.com/goshuh/flexus_misc
```

## Setting up environement
```bash
export FLEXUS_ROOT $(realpath flexus)
```

## Building QEMU

```sh
cd midgard_qemu
./configure --target-list=riscv64-softmmu
cd build
ninja
```

If you encounter the problem `undefined reference to symbol dlsym@@GLIBC_2.2.5`, please use the following commands to [configure](https://stackoverflow.com/questions/67667369/undefined-reference-to-symbol-dlsymglibc-2-2-5) QEMU:

```sh
./configure --target-list=riscv64-softmmu --extra-ldflags='-Wl,--no-as-needed,-ldl'
```

## Building FLEXUS
```sh
cd flexus_misc
# you only need this once before invoking build
./build KeenKraken # trace simulator, or
make -C KeenKraken
./build KnottyKraken # timing simulator
make -C KnottyKraken
```

## Create symlinks
```sh
cd flexus_misc
ln -s ${PATH_TO_QEMU}/build/qemu-system-riscv64 qemu
```

# Run

## Normal QEMU

```sh
cd flexus_misc
./runq
```

The filesystem now contains basic tools provided by `/bin/busybox` like `ls`, `cd`, etc. It also contains a `/bin/media` file that is the workload that I am currently running.

When you think the simulation proceeds to the point you want, hit Ctrl-A + Ctrl-C to enter the QEMU monitor, and type the following commands:
```sh
stop # stops simulation first
savevm-external SNAPSHOT_NAME
```

After that you can type `cont` to continue the simulation or `q` to quit.

You can modify any command line arguments passed to QEMU in the `emu` file, which just writes those arguments in a prettier format.

## Trace simulation

```sh
cd flexus_misc
./runq +trace +snap=${SNAPSHOT_NAME}
```

The simulation log is saved in `debug.log` instead of being displayed in the terminal (the latter is broken). You can change parameters passed to FLEXUS in the `trace.cfg` file.

## Timing simulation

```sh
cd flexus_misc
./runq +timing +snap=${SNAPSHOT_NAME}
```

You can change parameters passed to FLEXUS in the `timing.cfg` file.

# Notes

These repos are updated frequently, so please also pull them frequently.
