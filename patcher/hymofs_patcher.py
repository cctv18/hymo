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
# 1. Patch fs/open.c (Core Logic & vfs_open)
# ==========================================
def patch_open_c(content):
    # Add necessary includes
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
    )
    
    if "HymoFS Hook" in content:
        return content

    content = re.sub(r'(#include <linux/syscalls.h>)', r'\1\n' + includes, content)

    # Core Hook Logic
    hook_code = (
        "\n/* HymoFS Hook - Dynamic Path Redirection */\n"
        "#define HYMO_HASH_BITS 10\n"
        "\n"
        "struct hymo_entry {\n"
        "    char *src;\n"
        "    char *target;\n"
        "    struct hlist_node node;\n"
        "};\n"
        "\n"
        "static DEFINE_HASHTABLE(hymo_paths, HYMO_HASH_BITS);\n"
        "static spinlock_t hymo_lock;\n"
        "static atomic_t hymo_version = ATOMIC_INIT(0);\n"
        "\n"
        "static void hymo_cleanup(void) {\n"
        "    struct hymo_entry *entry;\n"
        "    struct hlist_node *tmp;\n"
        "    int bkt;\n"
        "    hash_for_each_safe(hymo_paths, bkt, tmp, entry, node) {\n"
        "        hash_del(&entry->node);\n"
        "        kfree(entry->src);\n"
        "        kfree(entry->target);\n"
        "        kfree(entry);\n"
        "    }\n"
        "}\n"
        "\n"
        "/* Control interface: echo \"add /src /target\" > /proc/hymo_ctl */\n"
        "static ssize_t hymo_ctl_write(struct file *file, const char __user *buffer,\n"
        "                  size_t count, loff_t *pos)\n"
        "{\n"
        "    char *cmd, *p, *op, *src, *target;\n"
        "    unsigned long flags;\n"
        "    struct hymo_entry *entry;\n"
        "    struct hlist_node *tmp;\n"
        "    u32 hash;\n"
        "    bool found;\n"
        "\n"
        "    if (count > 8192) return -EINVAL;\n"
        "    cmd = kmalloc(count + 1, GFP_KERNEL);\n"
        "    if (!cmd) return -ENOMEM;\n"
        "    if (copy_from_user(cmd, buffer, count)) { kfree(cmd); return -EFAULT; }\n"
        "    cmd[count] = '\\0';\n"
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
        "        src = strsep(&p, \" \");\n"
        "        target = p;\n"
        "        if (src && target) {\n"
        "            target = strim(target);\n"
        "            hash = full_name_hash(NULL, src, strlen(src));\n"
        "            found = false;\n"
        "            hash_for_each_possible(hymo_paths, entry, node, hash) {\n"
        "                if (strcmp(entry->src, src) == 0) {\n"
        "                    kfree(entry->target);\n"
        "                    entry->target = kstrdup(target, GFP_ATOMIC);\n"
        "                    found = true;\n"
        "                    break;\n"
        "                }\n"
        "            }\n"
        "            if (!found) {\n"
        "                entry = kmalloc(sizeof(*entry), GFP_ATOMIC);\n"
        "                if (entry) {\n"
        "                    entry->src = kstrdup(src, GFP_ATOMIC);\n"
        "                    entry->target = kstrdup(target, GFP_ATOMIC);\n"
        "                    if (entry->src && entry->target) {\n"
        "                        hash_add(hymo_paths, &entry->node, hash);\n"
        "                    } else {\n"
        "                        kfree(entry->src); kfree(entry->target); kfree(entry);\n"
        "                    }\n"
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
        "    int bkt;\n"
        "    unsigned long flags;\n"
        "\n"
        "    seq_printf(m, \"HymoFS Version: %d\\n\", atomic_read(&hymo_version));\n"
        "    \n"
        "    spin_lock_irqsave(&hymo_lock, flags);\n"
        "    hash_for_each(hymo_paths, bkt, entry, node) {\n"
        "        seq_printf(m, \"%s -> %s\\n\", entry->src, entry->target);\n"
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
        "    proc_create(\"hymo_ctl\", 0660, NULL, &hymo_ctl_ops);\n"
        "    pr_info(\"HymoFS: initialized (map mode)\\n\");\n"
        "    return 0;\n"
        "}\n"
        "fs_initcall(hymofs_init);\n"
        "\n"
        "bool hymofs_redirect(const struct path *path, struct path *new_path)\n"
        "{\n"
        "    char *pathname, *buf;\n"
        "    bool redirected = false;\n"
        "    int ret;\n"
        "    unsigned long flags;\n"
        "    struct hymo_entry *entry;\n"
        "    u32 hash;\n"
        "\n"
        "    if (atomic_read(&hymo_version) == 0) return false;\n"
        "    if (unlikely(!path || !path->dentry || !path->mnt)) return false;\n"
        "\n"
        "    buf = kmalloc(PATH_MAX, GFP_KERNEL);\n"
        "    if (unlikely(!buf)) return false;\n"
        "\n"
        "    pathname = d_path(path, buf, PATH_MAX);\n"
        "    if (IS_ERR(pathname)) {\n"
        "        kfree(buf);\n"
        "        return false;\n"
        "    }\n"
        "\n"
        "    hash = full_name_hash(NULL, pathname, strlen(pathname));\n"
        "\n"
        "    spin_lock_irqsave(&hymo_lock, flags);\n"
        "    hash_for_each_possible(hymo_paths, entry, node, hash) {\n"
        "        if (strcmp(entry->src, pathname) == 0) {\n"
        "            /* Found mapping! */\n"
        "            char *target = kstrdup(entry->target, GFP_ATOMIC);\n"
        "            spin_unlock_irqrestore(&hymo_lock, flags);\n"
        "            \n"
        "            if (target) {\n"
        "                ret = kern_path(target, LOOKUP_FOLLOW, new_path);\n"
        "                if (ret == 0) {\n"
        "                    redirected = true;\n"
        "                    pr_debug(\"HymoFS: %s -> %s\\n\", pathname, target);\n"
        "                }\n"
        "                kfree(target);\n"
        "            }\n"
        "            goto out;\n"
        "        }\n"
        "    }\n"
        "    spin_unlock_irqrestore(&hymo_lock, flags);\n"
        "\n"
        "out:\n"
        "    kfree(buf);\n"
        "    return redirected;\n"
        "}\n"
        "EXPORT_SYMBOL(hymofs_redirect);\n"
        "\n"
        "static int hymofs_open(const struct path *path, struct file *file)\n"
        "{\n"
        "    struct path redirect_path;\n"
        "    const struct path *final_path = path;\n"
        "    int ret;\n"
        "\n"
        "    if (hymofs_redirect(path, &redirect_path))\n"
        "        final_path = &redirect_path;\n"
        "\n"
        "    file->f_path = *final_path;\n"
        "    ret = do_dentry_open(file, d_backing_inode(final_path->dentry), NULL);\n"
        "\n"
        "    if (final_path == &redirect_path)\n"
        "        path_put(&redirect_path);\n"
        "\n"
        "    return ret;\n"
        "}\n"
    )

    # Inject hook code before vfs_open
    pattern = r'(/\*\*\s+\*\s+vfs_open.*?\*/\s+)(int\s+vfs_open\([^)]+\)\s+\{[^}]+\})'
    
    def replace_vfs_open(match):
        return match.group(1) + hook_code + "\nint vfs_open(const struct path *path, struct file *file)\n{\n    return hymofs_open(path, file);\n}\n"

    return re.sub(pattern, replace_vfs_open, content, flags=re.DOTALL)

# ==========================================
# 2. Patch fs/stat.c (vfs_getattr)
# ==========================================
def patch_stat_c(content):
    # Ensure security.h is included for security_inode_getattr
    includes = "\n#include <linux/security.h>\nextern bool hymofs_redirect(const struct path *path, struct path *new_path);\n"
    
    if "hymofs_redirect" not in content:
        content = re.sub(r'(#include "internal.h")', r'\1' + includes, content)

    new_vfs_getattr = (
        "int vfs_getattr(const struct path *path, struct kstat *stat,\n"
        "                u32 request_mask, unsigned int query_flags)\n"
        "{\n"
        "    struct path redirect_path;\n"
        "    const struct path *final_path = path;\n"
        "    int retval;\n"
        "\n"
        "    if (WARN_ON_ONCE(query_flags & AT_GETATTR_NOSEC))\n"
        "        return -EPERM;\n"
        "\n"
        "    if (hymofs_redirect(path, &redirect_path))\n"
        "        final_path = &redirect_path;\n"
        "\n"
        "    retval = security_inode_getattr(final_path);\n"
        "    if (retval)\n"
        "        goto out;\n"
        "    retval = vfs_getattr_nosec(final_path, stat, request_mask, query_flags);\n"
        "out:\n"
        "    if (final_path == &redirect_path)\n"
        "        path_put(&redirect_path);\n"
        "    return retval;\n"
        "}\n"
        "EXPORT_SYMBOL_NS(vfs_getattr, ANDROID_GKI_VFS_EXPORT_ONLY);\n"
    )
    
    pattern = r'int\s+vfs_getattr\(const struct path \*path[^{]+\{[^}]*security_inode_getattr[^}]+return vfs_getattr_nosec[^}]+\}\s+EXPORT_SYMBOL[^;]+;'
    return re.sub(pattern, new_vfs_getattr, content, flags=re.DOTALL)

# ==========================================
# 3. Patch fs/namei.c (readlinkat -> vfs_readlink)
# ==========================================
def patch_namei_c(content):
    decl = "\nextern bool hymofs_redirect(const struct path *path, struct path *new_path);\n"
    if "hymofs_redirect" not in content:
        content = re.sub(r'(#include "internal.h")', r'\1' + decl, content)

    helper_func = (
        "\nstatic int hymofs_readlink(struct path *path, char __user *buf, int buflen)\n"
        "{\n"
        "    struct path redirect_path;\n"
        "    int ret;\n"
        "    if (hymofs_redirect(path, &redirect_path)) {\n"
        "        ret = vfs_readlink(redirect_path.dentry, buf, buflen);\n"
        "        path_put(&redirect_path);\n"
        "        return ret;\n"
        "    }\n"
        "    return vfs_readlink(path->dentry, buf, buflen);\n"
        "}\n"
    )
    
    content = re.sub(r'(static int do_readlinkat)', helper_func + r'\1', content)

    pattern = r'(error\s*=\s*)vfs_readlink\(path\.dentry,\s*buf,\s*buflen\);'
    content = re.sub(pattern, r'\1hymofs_readlink(&path, buf, buflen);', content)
    
    return content

# ==========================================
# 4. Patch fs/xattr.c (path_getxattr/listxattr)
# ==========================================
def patch_xattr_c(content):
    decl = "\nextern bool hymofs_redirect(const struct path *path, struct path *new_path);\n"
    if "hymofs_redirect" not in content:
        content = re.sub(r'(#include "internal.h")', r'\1' + decl, content)

    helper_get = (
        "\nstatic ssize_t hymo_path_getxattr(struct path *path, const char *name, void *value, size_t size)\n"
        "{\n"
        "    struct path redirect_path;\n"
        "    ssize_t ret;\n"
        "    if (hymofs_redirect(path, &redirect_path)) {\n"
        "        ret = vfs_getxattr(mnt_idmap(redirect_path.mnt), redirect_path.dentry, name, value, size);\n"
        "        path_put(&redirect_path);\n"
        "        return ret;\n"
        "    }\n"
        "    return vfs_getxattr(mnt_idmap(path->mnt), path->dentry, name, value, size);\n"
        "}\n"
    )
    
    helper_list = (
        "\nstatic ssize_t hymo_path_listxattr(struct path *path, char *list, size_t size)\n"
        "{\n"
        "    struct path redirect_path;\n"
        "    ssize_t ret;\n"
        "    if (hymofs_redirect(path, &redirect_path)) {\n"
        "        ret = vfs_listxattr(redirect_path.dentry, list, size);\n"
        "        path_put(&redirect_path);\n"
        "        return ret;\n"
        "    }\n"
        "    return vfs_listxattr(path->dentry, list, size);\n"
        "}\n"
    )

    content = re.sub(r'(static int path_getxattr)', helper_get + r'\1', content)
    content = re.sub(r'(static int path_listxattr)', helper_list + r'\1', content)

    pattern_get = r'(error\s*=\s*)vfs_getxattr\([^,]+,\s*path\.dentry,\s*name,\s*value,\s*size\);'
    content = re.sub(pattern_get, r'\1hymo_path_getxattr(&path, name, value, size);', content)

    pattern_list = r'(error\s*=\s*)vfs_listxattr\(path\.dentry,\s*list,\s*size\);'
    content = re.sub(pattern_list, r'\1hymo_path_listxattr(&path, list, size);', content)

    return content

# ==========================================
# Main Execution
# ==========================================
print(">>> HymoFS Patcher (Optimized Version) <<<")
patch_file('fs/open.c', 'vfs_open hook', patch_open_c)
patch_file('fs/stat.c', 'vfs_getattr hook', patch_stat_c)
patch_file('fs/namei.c', 'readlinkat hook', patch_namei_c)
patch_file('fs/xattr.c', 'xattr hooks', patch_xattr_c)
