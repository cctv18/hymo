# Hymo Kernel VFS Hook Module

实验性内核 VFS hook 功能,基于 [kernel-inline-hook-framework](https://github.com/WeiJiLab/kernel-inline-hook-framework)。

## 目标

通过内核 inline hook 技术在 VFS 层拦截和修改文件系统操作,实现比 OverlayFS 更底层的模块挂载机制。

## 架构

```
kernel_hook/
├── hymo_hook.c          # Hymo hook 模块主文件
├── hook_vfs_open.c      # hook vfs_open 函数
├── hook_do_mount.c      # hook do_mount 函数 (可选)
├── Makefile             # 内核模块构建文件
└── README.md            # 本文档
```

## 依赖

### 内核配置要求
- `CONFIG_KALLSYMS=y` ✅
- `CONFIG_KALLSYMS_ALL=y` ✅
- `CONFIG_KPROBES=y` ✅
- `CONFIG_MODULES=y` ✅
- `CONFIG_STACKTRACE=y` ✅

### 编译环境
- NDK r25c (与 Hymo 主程序相同)
- 目标内核版本: 6.6.66-android15
- 架构: arm64

## 构建

```bash
# 1. 先编译 hookFrame.ko
cd kernel_hook_framework/linux/src
make arm64 KDIR=/path/to/kernel/source CROSS_COMPILE=aarch64-linux-android-

# 2. 编译 Hymo hook 模块
cd kernel_hook
make KDIR=/path/to/kernel/source CROSS_COMPILE=aarch64-linux-android-
```

## 使用

```bash
# 1. 加载框架模块
adb push hookFrame.ko /data/local/tmp/
adb shell su -c "insmod /data/local/tmp/hookFrame.ko"

# 2. 加载 Hymo hook 模块
adb push hymoHook.ko /data/local/tmp/
adb shell su -c "insmod /data/local/tmp/hymoHook.ko"

# 3. 查看 hook 状态
adb shell su -c "cat /proc/hook_targets"

# 4. 动态控制
adb shell su -c "echo 'vfs_open 0' > /proc/hook_targets"  # 禁用
adb shell su -c "echo 'vfs_open 1' > /proc/hook_targets"  # 启用

# 5. 查看日志
adb shell su -c "dmesg | grep -i hymo"
```

## POC 目标

### 第一阶段: 基础验证
- [x] Hook `vfs_open` 函数
- [ ] 打印被打开的文件路径
- [ ] 验证 hook 机制正常工作

### 第二阶段: 路径重定向
- [ ] 检测是否访问模块目录
- [ ] 将路径重定向到 Hymo 的内容目录
- [ ] 测试基础模块挂载

### 第三阶段: 性能对比
- [ ] 对比 OverlayFS vs 内核 hook 的性能差异
- [ ] 测试稳定性和兼容性

## 风险评估

⚠️ **警告**: 这是实验性功能,存在以下风险:

1. **内核稳定性**: inline hook 修改内核代码段,可能导致系统崩溃
2. **兼容性**: 不同内核版本可能需要调整
3. **检测风险**: hook 行为可能被 SELinux/SafetyNet 检测
4. **维护成本**: 每次内核更新需要重新测试

## 参考资料

- [kernel-inline-hook-framework](https://github.com/WeiJiLab/kernel-inline-hook-framework)
- [Linux VFS 文档](https://www.kernel.org/doc/html/latest/filesystems/vfs.html)
- [Android 内核模块开发](https://source.android.com/devices/architecture/kernel)
