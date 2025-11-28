# Nuke Ext4 LKM

This directory contains the source code and pre-compiled binaries for the "Nuke Ext4" kernel module.

## Source & License
The source code (`src/nuke.c`) is derived from the [Mountify](https://github.com/backslashxx/mountify) project.
It is licensed under the **GPLv2**. A copy of the license is included in `src/LICENSE`.

## Usage
These kernel modules are used to unregister `ext4` sysfs nodes to improve stealth when using ext4 loop images.