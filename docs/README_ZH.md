# Hymo - 下一代 Android 混合挂载引擎

![Language](https://img.shields.io/badge/Language-C++-00599C?style=flat-square&logo=cplusplus)
![Platform](https://img.shields.io/badge/Platform-Android%20(KernelSU)-3DDC84?style=flat-square&logo=android)
![License](https://img.shields.io/badge/License-GPL--3.0-blue?style=flat-square)

> **Hymo** 是一个专为 KernelSU 设计的高性能混合挂载元模块。它采用原生 C++ 重构核心逻辑，引入劫持内核文件系统的HymoFS,不挂载而是直接使用VFS映射，以实现以假乱真的挂载效果。

---
**[ 🇺🇸/🇬🇧 English ](../README.md)**

## 核心架构 (Core Architecture)

Hymo 不仅仅是一个挂载脚本，它是一个完整的原生守护进程（Daemon），旨在解决传统 Shell 脚本在复杂挂载场景下的性能瓶颈与兼容性问题。

### 1. 原生 C++ 引擎
*   **高性能**：核心逻辑完全由 C++ 编写，摒弃了低效的 Shell 脚本调用。
*   **直接系统调用**：直接使用 `fsopen`, `fsconfig`, `fsmount`, `move_mount` 等现代 Linux Mount API，绕过 `mount` 命令行的限制，提供更精细的挂载控制。
*   **极速启动**：优化的执行流程使得模块加载几乎不增加系统启动时间。

### 2. HymoFS 与多模式引擎 (HymoFS & Multi-Mode Engine)
Hymo 引入了自创的 **HymoFS** 技术，构建了三级挂载策略：
*   **HymoFS (内核模式)**：对内核源码打补丁后开放一个内核接口，直接劫持底层文件系统实现文件映射而非挂载，可以实现热恢复。
*   **OverlayFS (通用模式)**：在标准环境下的首选方案，利用内核 OverlayFS 特性实现文件级合并。
*   **Magic Mount (兼容模式)**：针对旧内核或特殊分区的传统 Bind Mount 兜底方案。
*   **动态决策**：守护进程会自动检测环境选择最佳模式，用户也可通过 WebUI 强制指定。

### 3. 智能同步 (Smart Sync)
*   **增量更新**：启动时自动比对模块的 `module.prop` 和文件时间戳。
*   **零冗余 IO**：仅同步发生变更的模块文件到工作目录，大幅减少启动时的 I/O 压力，延长闪存寿命。

### 4. 弹性存储后端 (Smart Storage)
*   **智能空间管理**：安装时自动检测内核 Tmpfs 支持情况。如果支持，则跳过创建 Ext4 镜像，直接使用内存文件系统，节省用户存储空间。
*   **Tmpfs 优先**：运行时优先在内存中构建模块镜像，速度最快且重启即焚（高隐藏性）。
*   **Ext4 镜像回退**：仅在内核不支持 Tmpfs 时自动回退到 `modules.img` 环回镜像，确保功能可用性。

---


## 编译与安装 (Build & Install)

Hymo 使用标准的 Makefile 构建系统，支持交叉编译。

**前置要求**：
*   Android NDK (r25+)
*   Node.js & npm (用于构建 WebUI)
*   Make & Zip

**HymoFS补丁**

如果需要使用HymoFS,请在编译内核时在编译脚本中加入：
```bash
wget https://raw.githubusercontent.com/Anatdx/HymoFS/refs/heads/main/patch/hymofs.patch
patch -p1 -F 3 < hymofs.patch
echo "CONFIG_HYMOFS=y" >> ./common/arch/arm64/configs/gki_defconfig # Write to defconfig
```
或者如果你用SUSFS,请把在编译脚本中这段放到SUSFS补丁的**后面**：
```bash
wget https://raw.githubusercontent.com/Anatdx/HymoFS/refs/heads/main/patch/hymofs_with_susfs.patch
patch -p1 -F 3 < hymofs_with_susfs.patch
echo "CONFIG_HYMOFS=y" >> ./common/arch/arm64/configs/gki_defconfig # Write to defconfig
```

**编译命令**：
```bash
# 编译所有架构并打包
make zip

# 仅编译 arm64 并生成测试包
make testzip
```

**安装**：
生成的 zip 包可直接在 KernelSU Manager 中刷入。

---

## 命令行工具 (CLI Usage)

Hymo 提供了一个强大的命令行工具 `hymod`，用于管理守护进程和 HymoFS 规则。

### 基本用法
```bash
hymod [选项] [命令]
```

### 命令列表
*   `mount`: 挂载所有模块（默认操作）。
*   `modules`: 列出所有活跃的模块。
*   `storage`: 显示当前存储状态 (Tmpfs/Ext4)。
*   `reload`: 重载 HymoFS 映射（扫描变更）。
*   `clear`: 清空所有 HymoFS 映射（紧急重置）。
*   `list`: 列出所有活跃的 HymoFS 内核规则。
*   `version`: 显示 HymoFS 协议和配置版本。
*   `gen-config`: 生成默认配置文件。
*   `show-config`: 显示当前配置。
*   `add <mod_id>`: 手动添加指定模块的规则。
*   `delete <mod_id>`: 手动删除指定模块的规则。
*   `raw <cmd> ...`: 执行原始 HymoFS 底层命令 (add/hide/inject/delete)。

### 选项
*   `-c, --config FILE`: 指定自定义配置文件路径。
*   `-m, --moduledir DIR`: 指定模块目录（默认：`/data/adb/modules`）。
*   `-v, --verbose`: 启用详细日志以进行调试。
*   `-p, --partition NAME`: 添加要扫描的分区（可多次使用）。

---

## 致谢 (Credits)

*   **Meta-Hybrid Mount**: 本项目的灵感来源与原型基础。
*   **KernelSU**: 强大的 Root 解决方案。
*   **Libcxx**: Android NDK C++ 标准库。
*   **所有本项目的贡献者**: 感谢你们的付出。

---

> **免责声明**: 本项目涉及系统底层修改，请在确保数据备份的前提下使用。开发者不对因使用本模块导致的任何数据丢失或设备损坏负责。
