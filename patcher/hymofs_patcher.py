import re
import sys

def patch_file(filepath, description, patch_func):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        new_content = patch_func(content)
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"  [✓] {filepath} patched ({description})")
        else:
            print(f"  [!] {filepath} not changed (pattern not found or already patched?)")
            
    except Exception as e:
        print(f"  [✗] Failed to patch {filepath}: {e}")
        sys.exit(1)

# ==========================================
# 1. Patch fs/open.c (The Brain)
# ==========================================
def patch_open_c(content):
    includes = (
        "#include <linux/proc_fs.h>\n"
        "#include <linux/uaccess.h>\n"
        "#include <linux/slab.h>\n"
        "#include <linux/namei.h>\n"
        "#include <linux/dcache.h>\n"
        "#include <linux/mount.h>\n"
        "#include <linux/fs_struct.h>\n"
        "#include <linux/path.h>\n"
        "#include <linux/seq_file.h>\n"
        "#include <linux/hashtable.h>\n"
        "#include <linux/dirent.h>\n"
    )
    
    if "HymoFS God Mode" in content:
        return content

    content = re.sub(r'(#include <linux/syscalls.h>)', lambda m: m.group(1) + '\n' + includes, content)

    hook_code = (
        "\n/* HymoFS God Mode - Advanced Path Manipulation */\n"
        "#define HYMO_HASH_BITS 10\n"
        "\n"
        "struct hymo_entry {\n"
        "    char *src;\n"
        "    char *target;\n"
        "    struct hlist_node node;\n"
        "};\n"
        "\n"
        "struct hymo_hide_entry {\n"
        "    char *path;\n"
        "    struct hlist_node node;\n"
        "};\n"
        "\n"
        "static DEFINE_HASHTABLE(hymo_paths, HYMO_HASH_BITS);\n"
        "static DEFINE_HASHTABLE(hymo_hide_paths, HYMO_HASH_BITS);\n"
        "static DEFINE_SPINLOCK(hymo_lock);\n"
        "static atomic_t hymo_version = ATOMIC_INIT(0);\n"
        "\n"
        "static void hymo_cleanup(void) {\n"
        "    struct hymo_entry *entry;\n"
        "    struct hymo_hide_entry *hide_entry;\n"
        "    struct hlist_node *tmp;\n"
        "    int bkt;\n"
        "    hash_for_each_safe(hymo_paths, bkt, tmp, entry, node) {\n"
        "        hash_del(&entry->node);\n"
        "        kfree(entry->src);\n"
        "        kfree(entry->target);\n"
        "        kfree(entry);\n"
        "    }\n"
        "    hash_for_each_safe(hymo_hide_paths, bkt, tmp, hide_entry, node) {\n"
        "        hash_del(&hide_entry->node);\n"
        "        kfree(hide_entry->path);\n"
        "        kfree(hide_entry);\n"
        "    }\n"
        "}\n"
        "\n"
        "/* Control interface: \n"
        "   echo \"add /src /target\" > /proc/hymo_ctl\n"
        "   echo \"hide /path/to/hide\" > /proc/hymo_ctl\n"
        "   echo \"clear\" > /proc/hymo_ctl\n"
        "*/\n"
        "static ssize_t hymo_ctl_write(struct file *file, const char __user *buffer,\n"
        "                  size_t count, loff_t *pos)\n"
        "{\n"
        "    char *cmd, *p, *op, *arg1, *arg2;\n"
        "    unsigned long flags;\n"
        "    struct hymo_entry *entry;\n"
        "    struct hymo_hide_entry *hide_entry;\n"
        "    u32 hash;\n"
        "    bool found;\n"
        "\n"
        "    if (count > 8192) return -EINVAL;\n"
        "    cmd = kmalloc(count + 1, GFP_KERNEL);\n"
        "    if (!cmd) return -ENOMEM;\n"
        "    if (copy_from_user(cmd, buffer, count)) { kfree(cmd); return -EFAULT; }\n"
        "    cmd[count] = 0;\n"
        "\n"
        "    p = strim(cmd);\n"
        "    op = strsep(&p, \" \");\n"
        "    if (!op) { kfree(cmd); return -EINVAL; }\n"
        "\n"
        "    spin_lock_irqsave(&hymo_lock, flags);\n"
        "\n"
        "    if (strcmp(op, \"clear\") == 0) {\n"
        "        hymo_cleanup();\n"
        "        atomic_inc(&hymo_version);\n"
        "    } else if (strcmp(op, \"add\") == 0) {\n"
        "        arg1 = strsep(&p, \" \");\n"
        "        arg2 = p;\n"
        "        if (arg1 && arg2) {\n"
        "            arg2 = strim(arg2);\n"
        "            hash = full_name_hash(NULL, arg1, strlen(arg1));\n"
        "            found = false;\n"
        "            hash_for_each_possible(hymo_paths, entry, node, hash) {\n"
        "                if (strcmp(entry->src, arg1) == 0) {\n"
        "                    kfree(entry->target);\n"
        "                    entry->target = kstrdup(arg2, GFP_ATOMIC);\n"
        "                    found = true;\n"
        "                    break;\n"
        "                }\n"
        "            }\n"
        "            if (!found) {\n"
        "                entry = kmalloc(sizeof(*entry), GFP_ATOMIC);\n"
        "                if (entry) {\n"
        "                    entry->src = kstrdup(arg1, GFP_ATOMIC);\n"
        "                    entry->target = kstrdup(arg2, GFP_ATOMIC);\n"
        "                    if (entry->src && entry->target) hash_add(hymo_paths, &entry->node, hash);\n"
        "                    else { kfree(entry->src); kfree(entry->target); kfree(entry); }\n"
        "                }\n"
        "            }\n"
        "            atomic_inc(&hymo_version);\n"
        "        }\n"
        "    } else if (strcmp(op, \"hide\") == 0) {\n"
        "        arg1 = p;\n"
        "        if (arg1) {\n"
        "            arg1 = strim(arg1);\n"
        "            hash = full_name_hash(NULL, arg1, strlen(arg1));\n"
        "            found = false;\n"
        "            hash_for_each_possible(hymo_hide_paths, hide_entry, node, hash) {\n"
        "                if (strcmp(hide_entry->path, arg1) == 0) {\n"
        "                    found = true;\n"
        "                    break;\n"
        "                }\n"
        "            }\n"
        "            if (!found) {\n"
        "                hide_entry = kmalloc(sizeof(*hide_entry), GFP_ATOMIC);\n"
        "                if (hide_entry) {\n"
        "                    hide_entry->path = kstrdup(arg1, GFP_ATOMIC);\n"
        "                    if (hide_entry->path) hash_add(hymo_hide_paths, &hide_entry->node, hash);\n"
        "                    else kfree(hide_entry);\n"
        "                }\n"
        "            }\n"
        "            atomic_inc(&hymo_version);\n"
        "        }\n"
        "    }\n"
        "\n"
        "    spin_unlock_irqrestore(&hymo_lock, flags);\n"
        "    kfree(cmd);\n"
        "    return count;\n"
        "}\n"
        "\n"
        "static int hymo_ctl_show(struct seq_file *m, void *v)\n"
        "{\n"
        "    struct hymo_entry *entry;\n"
        "    struct hymo_hide_entry *hide_entry;\n"
        "    int bkt;\n"
        "    unsigned long flags;\n"
        "\n"
        "    seq_printf(m, \"HymoFS Version: %d\\n\", atomic_read(&hymo_version));\n"
        "    \n"
        "    spin_lock_irqsave(&hymo_lock, flags);\n"
        "    hash_for_each(hymo_paths, bkt, entry, node) {\n"
        "        seq_printf(m, \"add %s -> %s\\n\", entry->src, entry->target);\n"
        "    }\n"
        "    hash_for_each(hymo_hide_paths, bkt, hide_entry, node) {\n"
        "        seq_printf(m, \"hide %s\\n\", hide_entry->path);\n"
        "    }\n"
        "    spin_unlock_irqrestore(&hymo_lock, flags);\n"
        "    return 0;\n"
        "}\n"
        "\n"
        "static int hymo_ctl_open(struct inode *inode, struct file *file)\n"
        "{\n"
        "    return single_open(file, hymo_ctl_show, NULL);\n"
        "}\n"
        "\n"
        "static const struct proc_ops hymo_ctl_ops = {\n"
        "    .proc_open    = hymo_ctl_open,\n"
        "    .proc_read    = seq_read,\n"
        "    .proc_lseek   = seq_lseek,\n"
        "    .proc_release = single_release,\n"
        "    .proc_write   = hymo_ctl_write,\n"
        "};\n"
        "\n"
        "static int __init hymofs_init(void)\n"
        "{\n"
        "    spin_lock_init(&hymo_lock);\n"
        "    hash_init(hymo_paths);\n"
        "    hash_init(hymo_hide_paths);\n"
        "    proc_create(\"hymo_ctl\", 0660, NULL, &hymo_ctl_ops);\n"
        "    pr_info(\"HymoFS: initialized (God Mode v3)\\n\");\n"
        "    return 0;\n"
        "}\n"
        "fs_initcall(hymofs_init);\n"
        "\n"
        "/* Returns kstrdup'd target if found, NULL otherwise. Caller must kfree. */\n"
        "char *hymofs_resolve_target(const char *pathname)\n"
        "{\n"
        "    unsigned long flags;\n"
        "    struct hymo_entry *entry;\n"
        "    u32 hash;\n"
        "    char *target = NULL;\n"
        "\n"
        "    if (atomic_read(&hymo_version) == 0) return NULL;\n"
        "    if (!pathname) return NULL;\n"
        "\n"
        "    hash = full_name_hash(NULL, pathname, strlen(pathname));\n"
        "\n"
        "    spin_lock_irqsave(&hymo_lock, flags);\n"
        "    hash_for_each_possible(hymo_paths, entry, node, hash) {\n"
        "        if (strcmp(entry->src, pathname) == 0) {\n"
        "            target = kstrdup(entry->target, GFP_ATOMIC);\n"
        "            break;\n"
        "        }\n"
        "    }\n"
        "    spin_unlock_irqrestore(&hymo_lock, flags);\n"
        "    return target;\n"
        "}\n"
        "EXPORT_SYMBOL(hymofs_resolve_target);\n"
        "\n"
        "bool hymofs_should_hide(const char *pathname)\n"
        "{\n"
        "    unsigned long flags;\n"
        "    struct hymo_hide_entry *entry;\n"
        "    u32 hash;\n"
        "    bool found = false;\n"
        "\n"
        "    if (atomic_read(&hymo_version) == 0) return false;\n"
        "    if (!pathname) return false;\n"
        "\n"
        "    hash = full_name_hash(NULL, pathname, strlen(pathname));\n"
        "\n"
        "    spin_lock_irqsave(&hymo_lock, flags);\n"
        "    hash_for_each_possible(hymo_hide_paths, entry, node, hash) {\n"
        "        if (strcmp(entry->path, pathname) == 0) {\n"
        "            found = true;\n"
        "            break;\n"
        "        }\n"
        "    }\n"
        "    spin_unlock_irqrestore(&hymo_lock, flags);\n"
        "    return found;\n"
        "}\n"
        "EXPORT_SYMBOL(hymofs_should_hide);\n"
    )

    pattern = r'(#include <linux/hashtable.h>)'
    return re.sub(pattern, lambda m: m.group(1) + hook_code, content, flags=re.DOTALL)

# ==========================================
# 2. Patch fs/namei.c (Lookup Hook)
# ==========================================
def patch_namei_c(content):
    decl = "\nextern char *hymofs_resolve_target(const char *pathname);\nextern bool hymofs_should_hide(const char *pathname);\n"
    if "hymofs_resolve_target" not in content:
        content = re.sub(r'(#include <linux/fs.h>)', lambda m: m.group(1) + decl, content)

    if "getname_flags(" in content and "__original_getname_flags" not in content:
        content = re.sub(r'^getname_flags\(', r'__original_getname_flags(', content, flags=re.MULTILINE)
        
        wrapper = (
            "struct filename *__original_getname_flags(const char __user *filename, int flags, int *empty);\n"
            "\n"
            "struct filename *getname_flags(const char __user *filename, int flags, int *empty)\n"
            "{\n"
            "    struct filename *result = __original_getname_flags(filename, flags, empty);\n"
            "    char *target;\n"
            "\n"
            "    if (IS_ERR(result)) return result;\n"
            "\n"
            "    /* HymoFS God Mode Hook */\n"
            "    if (hymofs_should_hide(result->name)) {\n"
            "        putname(result);\n"
            "        /* Return ENOENT directly */\n"
            "        return ERR_PTR(-ENOENT);\n"
            "    } else {\n"
            "        target = hymofs_resolve_target(result->name);\n"
            "        if (target) {\n"
            "            putname(result);\n"
            "            result = getname_kernel(target);\n"
            "            kfree(target);\n"
            "        }\n"
            "    }\n"
            "    return result;\n"
            "}\n"
        )
        
        content = re.sub(r'(struct filename \*\s+__original_getname_flags)', lambda m: wrapper + '\n' + m.group(1), content)

    return content

# ==========================================
# 3. Patch fs/readdir.c (Listing Hook)
# ==========================================
def patch_readdir_c(content):
    # Add includes and externs
    if "hymofs_should_hide" not in content:
        includes = (
            "\n#include <linux/namei.h>\n"
            "#include <linux/dcache.h>\n"
            "extern bool hymofs_should_hide(const char *pathname);\n"
        )
        content = re.sub(r'(#include <linux/uaccess.h>)', lambda m: m.group(1) + includes, content)

    # Inject fields into structs (getdents_callback, getdents_callback64, compat_getdents_callback)
    # We look for 'struct dir_context ctx;' and append our fields
    new_fields = (
        "struct dir_context ctx;\n"
        "\tstruct file *file;\n"
        "\tchar *path_buf;\n"
        "\tchar *dir_path;\n"
        "\tint dir_path_len;"
    )
    if "struct file *file;" not in content:
        content = re.sub(r'struct dir_context ctx;', new_fields, content)

    # Modify filldir/filldir64/compat_filldir to check hiding using pre-calculated path
    hide_check = (
        "\n\tif (buf->dir_path) {\n"
        "\t\tint name_len = strlen(name);\n"
        "\t\tif (buf->dir_path_len + 1 + name_len < PAGE_SIZE) {\n"
        "\t\t\tchar *p = buf->path_buf + buf->dir_path_len;\n"
        "\t\t\tif (p > buf->path_buf && p[-1] != '/') *p++ = '/';\n"
        "\t\t\tmemcpy(p, name, name_len);\n"
        "\t\t\tp[name_len] = '\\0';\n"
        "\t\t\tif (hymofs_should_hide(buf->path_buf)) return true;\n"
        "\t\t}\n"
        "\t}\n"
    )
    
    # Inject check before verify_dirent_name
    if "if (buf->dir_path)" not in content:
        content = re.sub(r'(buf->error = verify_dirent_name\(name, namlen\);)', lambda m: hide_check + '\n\t' + m.group(1), content)

    # Modify SYSCALL_DEFINE3(getdents), getdents64, and COMPAT... to init/cleanup
    
    # Init logic
    init_code = (
        "\n\tif (!f.file)\n"
        "\t\treturn -EBADF;\n"
        "\tbuf.file = f.file;\n"
        "\tbuf.path_buf = (char *)__get_free_page(GFP_KERNEL);\n"
        "\tbuf.dir_path = NULL;\n"
        "\tif (buf.path_buf) {\n"
        "\t\tchar *p = d_path(&f.file->f_path, buf.path_buf, PAGE_SIZE);\n"
        "\t\tif (!IS_ERR(p)) {\n"
        "\t\t\tint len = strlen(p);\n"
        "\t\t\tmemmove(buf.path_buf, p, len + 1);\n"
        "\t\t\tbuf.dir_path = buf.path_buf;\n"
        "\t\t\tbuf.dir_path_len = len;\n"
        "\t\t} else {\n"
        "\t\t\tfree_page((unsigned long)buf.path_buf);\n"
        "\t\t\tbuf.path_buf = NULL;\n"
        "\t\t}\n"
        "\t}\n"
    )
    
    if "buf.path_buf = (char *)__get_free_page" not in content:
        content = re.sub(r'(if \(!f\.file\)\s+return -EBADF;)', init_code, content)

    # Cleanup logic
    cleanup_code = (
        "\n\tif (buf.path_buf) free_page((unsigned long)buf.path_buf);\n"
        "\tfdput_pos(f);"
    )
    
    if "if (buf.path_buf) free_page" not in content:
        content = re.sub(r'(fdput_pos\(f\);)', cleanup_code, content)

    return content

# ==========================================
# Main Execution
# ==========================================
print(">>> HymoFS Patcher (God Mode v3.2 - Bootloop Fix) <<<")
patch_file('fs/open.c', 'Core Logic & Hiding', patch_open_c)
patch_file('fs/namei.c', 'Lookup Hook (ENOENT Fix)', patch_namei_c)
patch_file('fs/readdir.c', 'Listing Hook (Optimized)', patch_readdir_c)
