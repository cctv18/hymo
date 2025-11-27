## v0.2.2-@c3d0af0-gc3d0af0

Changes since v0.2.2-@2a2b1c2a22b3831e5ad8e56e17ad0fc79f7e3925:
* Merge pull request #2 from YuzakiKokuban/feature/xtask-build
* 	deleted:    src/engine.rs 	deleted:    src/logger.rs 	modified:   src/main.rs 	deleted:    src/scanner.rs 	modified:   src/utils.rs
*     modified:   src/engine.rs 	modified:   src/logger.rs 	modified:   src/main.rs 	modified:   src/scanner.rs
* fix(xtask): clean up unused imports
* fix(xtask): correct module file copy destination
* 	modified:   xtask/src/main.rs
* build: temporarily disable zakosign integration
* fix(xtask): disable unnecessary android builds for zakosign
* ci: optimize workflows and fix xtask invocation
* 	modified:   xtask/src/main.rs
* fix(xtask): resolve duplicate code and compilation errors
* fix(xtask): correct zakosign build dependency order
* 	modified:   xtask/src/main.rs
* Merge pull request #1 from YuzakiKokuban/feature/WebUI
* feat: add zakosign
* 	modified:   src/logger.rs
* 	modified:   xtask/src/main.rs
* 	modified:   xtask/src/main.rs 	modified:   xtask/src/zip_ext.rs
* 	modified:   .github/workflows/build.yml 	modified:   .github/workflows/release.yml 	modified:   Cargo.toml
* 	modified:   .github/workflows/build.yml
* build: migrate to cargo-xtask and integrate zakosign
* refactor(core): migrate logging system to tracing
* refactor(core): modularize main logic into scanner and engine
* 	modified:   .github/workflows/build.yml
* style(webui): decouple styles into separate css files and fix file naming
* 	modified:   .github/workflows/build.yml
* [skip ci] Update KernelSU json and changelog for v0.2.2-@2a2b1c2a22b3831e5ad8e56e17ad0fc79f7e3925