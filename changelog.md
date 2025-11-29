## v0.2.6-@060b70d-g060b70d

Changes since v0.2.6-@3f15668:
* fix(core): resolve build error in utils and unused import in storage
* 	modified:   Cargo.toml
* refactor(core): implement centralized JSON state management and update consumers
* fix(core): remove unused dynamic mount point functions to resolve build warnings
* feat(installer): disable ext4 journal on image creation to prevent jbd2 detection
* perf: replace system allocator with mimalloc for improved performance
* fix(core): prune stale or disabled modules from storage during sync to prevent zombie mounts
* fix(core): disable dynamic decoy mount point and enforce static path at /data/adb/meta-hybrid/mnt
* [skip ci] Update KernelSU json and changelog for v0.2.6-@3f15668