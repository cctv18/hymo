#include "../kernel_hook_framework/linux/src/include/common_data.h"
#include <linux/fs.h>
#include <linux/path.h>
#include <linux/dcache.h>
#include <linux/printk.h>

// 定义 hook 模板
HOOK_FUNC_TEMPLATE(vfs_open);

// Hook 函数: 拦截 vfs_open
__nocfi int hook_vfs_open(const struct path *path, struct file *file)
{
	char *pathname = NULL;
	char *buf = NULL;
	char *origin_vfs_open;
	int ret;

	// 分配缓冲区用于获取路径
	buf = (char *)kmalloc(PATH_MAX, GFP_KERNEL);
	if (buf) {
		pathname = d_path(path, buf, PATH_MAX);
		if (!IS_ERR(pathname)) {
			// 打印被打开的文件路径
			printk(KERN_INFO "[Hymo Hook] vfs_open: %s\n", pathname);

			// TODO: 在这里可以实现路径重定向逻辑
			// 例如: 如果路径匹配 /system/app/XXX, 重定向到 /data/adb/hymo/modules/XXX/system/app/XXX
		}
		kfree(buf);
	}

	// 调用原始 vfs_open 函数
	origin_vfs_open = GET_CODESPACE_ADDERSS(vfs_open);
	ret = ((int (*)(const struct path *, struct file *))origin_vfs_open)(path, file);

	return ret;
}

static void *vfs_open_fn = NULL;

int hook_vfs_open_init(void)
{
	int ret = -EFAULT;

	// 查找 vfs_open 函数地址
	vfs_open_fn = (void *)find_func("vfs_open");
	if (!vfs_open_fn) {
		printk(KERN_ALERT "[Hymo Hook] Cannot find vfs_open function!\n");
		goto out;
	}

	printk(KERN_INFO "[Hymo Hook] Found vfs_open at %px\n", vfs_open_fn);

	// 准备 hook
	if (HIJACK_TARGET_PREP_HOOK(vfs_open_fn, vfs_open)) {
		printk(KERN_ALERT "[Hymo Hook] vfs_open prepare error!\n");
		goto out;
	}

	// 启用 hook
	if (hijack_target_enable(vfs_open_fn)) {
		printk(KERN_ALERT "[Hymo Hook] vfs_open enable error!\n");
		goto out;
	}

	printk(KERN_INFO "[Hymo Hook] vfs_open hooked successfully!\n");
	return 0;

out:
	hijack_target_disable(vfs_open_fn, true);
	return ret;
}

void hook_vfs_open_exit(void)
{
	if (vfs_open_fn) {
		hijack_target_disable(vfs_open_fn, true);
		printk(KERN_INFO "[Hymo Hook] vfs_open hook disabled\n");
	}
}
