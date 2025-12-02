obj-m += hymoHook.o

hymoHook-y += hymo_hook.o
hymoHook-y += hook_vfs_open.o

PWD := $(shell pwd)
KBUILD_EXTRA_SYMBOLS = $(PWD)/../kernel_hook_framework/linux/src/Module.symvers

default:
	@echo "Usage: make KDIR=/path/to/kernel/source CROSS_COMPILE=aarch64-linux-android-"
	@echo ""
	@echo "Example for Android kernel 6.6:"
	@echo "  make KDIR=/path/to/kernel-6.6 CROSS_COMPILE=\$${NDK}/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android-"
	@echo ""
	@echo "Note: You must build hookFrame.ko first!"
	@echo "  cd ../kernel_hook_framework/linux/src"
	@echo "  make arm64 KDIR=/path/to/kernel/source CROSS_COMPILE=..."

arm64: check
	$(MAKE) ARCH=arm64 CROSS_COMPILE=$(CROSS_COMPILE) -C $(KDIR) M=$(PWD) modules

check:
ifndef KDIR
	$(error KDIR is not set. Please provide kernel source path: KDIR=/path/to/kernel)
endif
ifndef CROSS_COMPILE
	$(error CROSS_COMPILE is not set. Please provide toolchain prefix)
endif
	@if [ ! -f ../kernel_hook_framework/linux/src/Module.symvers ]; then \
		echo "Error: hookFrame.ko not built yet!"; \
		echo "Please build it first:"; \
		echo "  cd ../kernel_hook_framework/linux/src"; \
		echo "  make arm64 KDIR=$(KDIR) CROSS_COMPILE=$(CROSS_COMPILE)"; \
		exit 1; \
	fi

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
	rm -f *.ko *.o *.mod.c *.order *.symvers .*.cmd

install: arm64
	adb push hymoHook.ko /data/local/tmp/
	@echo ""
	@echo "Module pushed to device. To load:"
	@echo "  adb shell su -c 'insmod /data/local/tmp/hookFrame.ko'"
	@echo "  adb shell su -c 'insmod /data/local/tmp/hymoHook.ko'"

.PHONY: default arm64 check clean install
