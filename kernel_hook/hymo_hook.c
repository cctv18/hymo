#include <linux/module.h>
#include <linux/printk.h>

MODULE_AUTHOR("Hymo Project");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Hymo Kernel VFS Hook Module");

extern int hook_vfs_open_init(void);
extern void hook_vfs_open_exit(void);
extern void hijack_target_disable_all(bool, char *);

static int __init hymo_hook_init(void)
{
	int ret = -EFAULT;

	printk(KERN_INFO "[Hymo Hook] Loading Hymo kernel hook module...\n");

	// 初始化 vfs_open hook
	if (hook_vfs_open_init()) {
		printk(KERN_ALERT "[Hymo Hook] Failed to initialize vfs_open hook\n");
		goto out;
	}

	printk(KERN_INFO "[Hymo Hook] Module loaded successfully!\n");
	return 0;

out:
	hook_vfs_open_exit();
	return ret;
}

static void __exit hymo_hook_exit(void)
{
	// 禁用所有 hook
	hijack_target_disable_all(true, module_name(THIS_MODULE));
	
	printk(KERN_INFO "[Hymo Hook] Module unloaded\n");
}

module_init(hymo_hook_init);
module_exit(hymo_hook_exit);
