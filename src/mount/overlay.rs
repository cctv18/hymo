// Overlayfs mounting implementation
// Migrated from ksud/src/mount.rs and ksud/src/init_event.rs

use anyhow::{Context, Result, bail};
use log::{info, warn};
use std::path::{Path, PathBuf};

use procfs::process::Process;
use rustix::{fd::AsFd, fs::CWD, mount::*};

use crate::defs::KSU_OVERLAY_SOURCE;
use crate::utils::send_unmountable;

fn try_fsopen_mount(
    lowerdir_config: &str,
    upperdir: Option<&str>,
    workdir: Option<&str>,
    dest: &Path,
    override_creds: bool,
) -> Result<()> {
    let fs = fsopen("overlay", FsOpenFlags::FSOPEN_CLOEXEC)?;
    let fs_fd = fs.as_fd();
    
    fsconfig_set_string(fs_fd, "lowerdir", lowerdir_config)?;
    if let (Some(upperdir), Some(workdir)) = (upperdir, workdir) {
        fsconfig_set_string(fs_fd, "upperdir", upperdir)?;
        fsconfig_set_string(fs_fd, "workdir", workdir)?;
    }
    fsconfig_set_string(fs_fd, "source", KSU_OVERLAY_SOURCE)?;
    
    if override_creds {
        fsconfig_set_string(fs_fd, "override_creds", "off")?;
    }

    fsconfig_create(fs_fd)?;
    let mount = fsmount(fs_fd, FsMountFlags::FSMOUNT_CLOEXEC, MountAttrFlags::empty())?;
    move_mount(
        mount.as_fd(),
        "",
        CWD,
        dest,
        MoveMountFlags::MOVE_MOUNT_F_EMPTY_PATH,
    )?;
    Ok(())
}

fn try_legacy_mount(
    data: &str,
    dest: &Path,
) -> Result<()> {
    mount(
        KSU_OVERLAY_SOURCE,
        dest,
        "overlay",
        MountFlags::empty(),
        data,
    )?;
    Ok(())
}

pub fn mount_overlayfs(
    lower_dirs: &[String],
    lowest: &str,
    upperdir: Option<PathBuf>,
    workdir: Option<PathBuf>,
    dest: impl AsRef<Path>,
    disable_umount: bool,
) -> Result<()> {
    let lowerdir_config = lower_dirs
        .iter()
        .map(|s| s.as_ref())
        .chain(std::iter::once(lowest))
        .collect::<Vec<_>>()
        .join(":");
        
    info!(
        "mount overlayfs on {:?}, lowerdir={}, upperdir={:?}, workdir={:?}",
        dest.as_ref(),
        lowerdir_config,
        upperdir,
        workdir
    );

    let upper_str = upperdir
        .as_ref()
        .filter(|up| up.exists())
        .map(|e| e.display().to_string());
    let work_str = workdir
        .as_ref()
        .filter(|wd| wd.exists())
        .map(|e| e.display().to_string());

    // 1. Try fsopen with override_creds=off
    let mut result = try_fsopen_mount(
        &lowerdir_config, 
        upper_str.as_deref(), 
        work_str.as_deref(), 
        dest.as_ref(), 
        true
    );

    // 2. Fallback: Try fsopen WITHOUT override_creds (for older kernels)
    if result.is_err() {
        // debug!("fsopen with override_creds failed, retrying without...");
        result = try_fsopen_mount(
            &lowerdir_config, 
            upper_str.as_deref(), 
            work_str.as_deref(), 
            dest.as_ref(), 
            false
        );
    }

    // 3. Fallback: Legacy mount() syscall
    if let Err(e) = result {
        warn!("fsopen mount failed: {e:#}, fallback to legacy mount");
        
        let base_data = format!("lowerdir={lowerdir_config}");
        let mut data = base_data.clone();
        
        if let (Some(u), Some(w)) = (&upper_str, &work_str) {
            data = format!("{data},upperdir={u},workdir={w}");
        }

        // Try legacy with override_creds=off
        let data_secure = format!("{data},override_creds=off");
        if try_legacy_mount(&data_secure, dest.as_ref()).is_err() {
            // Final fallback: just basic options
            try_legacy_mount(&data, dest.as_ref())?;
        }
    }
    
    // Apply try_umount logic to overlay mounts as well
    if !disable_umount {
        let _ = send_unmountable(dest.as_ref());
    }
    
    Ok(())
}

pub fn bind_mount(from: impl AsRef<Path>, to: impl AsRef<Path>, disable_umount: bool) -> Result<()> {
    info!(
        "bind mount {} -> {}",
        from.as_ref().display(),
        to.as_ref().display()
    );
    let tree = open_tree(
        CWD,
        from.as_ref(),
        OpenTreeFlags::OPEN_TREE_CLOEXEC
            | OpenTreeFlags::OPEN_TREE_CLONE
            | OpenTreeFlags::AT_RECURSIVE,
    )?;
    move_mount(
        tree.as_fd(),
        "",
        CWD,
        to.as_ref(),
        MoveMountFlags::MOVE_MOUNT_F_EMPTY_PATH,
    )?;
    
    // Apply try_umount logic to bind mounts
    if !disable_umount {
        let _ = send_unmountable(to.as_ref());
    }
    
    Ok(())
}

fn mount_overlay_child(
    mount_point: &str,
    relative: &String,
    module_roots: &Vec<String>,
    stock_root: &String,
    disable_umount: bool,
) -> Result<()> {
    if !module_roots
        .iter()
        .any(|lower| Path::new(&format!("{lower}{relative}")).exists())
    {
        return bind_mount(stock_root, mount_point, disable_umount);
    }
    if !Path::new(&stock_root).is_dir() {
        return Ok(());
    }
    let mut lower_dirs: Vec<String> = vec![];
    for lower in module_roots {
        let lower_dir = format!("{lower}{relative}");
        let path = Path::new(&lower_dir);
        if path.is_dir() {
            lower_dirs.push(lower_dir);
        } else if path.exists() {
            // stock root has been blocked by this file
            return Ok(());
        }
    }
    if lower_dirs.is_empty() {
        return Ok(());
    }
    // merge modules and stock
    if let Err(e) = mount_overlayfs(&lower_dirs, stock_root, None, None, mount_point, disable_umount) {
        warn!("failed: {e:#}, fallback to bind mount");
        bind_mount(stock_root, mount_point, disable_umount)?;
    }
    Ok(())
}

pub fn mount_overlay(
    root: &String,
    module_roots: &Vec<String>,
    workdir: Option<PathBuf>,
    upperdir: Option<PathBuf>,
    disable_umount: bool,
) -> Result<()> {
    info!("mount overlay for {root}");
    if let Err(e) = std::env::set_current_dir(root) {
        warn!("failed to chdir to {root}: {e:#}");
        return Err(anyhow::anyhow!(e)); 
    }
    
    let stock_root = ".";

    // collect child mounts before mounting the root
    let mounts = Process::myself()?
        .mountinfo()
        .with_context(|| "get mountinfo")?;
    let mut mount_seq = mounts
        .0
        .iter()
        .filter(|m| {
            m.mount_point.starts_with(root) && !Path::new(&root).starts_with(&m.mount_point)
        })
        .map(|m| m.mount_point.to_str())
        .collect::<Vec<_>>();
    mount_seq.sort();
    mount_seq.dedup();

    mount_overlayfs(module_roots, root, upperdir, workdir, root, disable_umount)
        .with_context(|| "mount overlayfs for root failed")?;
        
    for mount_point in mount_seq.iter() {
        let Some(mount_point) = mount_point else {
            continue;
        };
        let relative = mount_point.replacen(root, "", 1);
        let stock_root: String = format!("{stock_root}{relative}");
        if !Path::new(&stock_root).exists() {
            continue;
        }
        if let Err(e) = mount_overlay_child(mount_point, &relative, module_roots, &stock_root, disable_umount) {
            warn!("failed to mount overlay for child {mount_point}: {e:#}, revert");
            umount_dir(root).with_context(|| format!("failed to revert {root}"))?;
            bail!(e);
        }
    }
    Ok(())
}

pub fn umount_dir(src: impl AsRef<Path>) -> Result<()> {
    unmount(src.as_ref(), UnmountFlags::empty())
        .with_context(|| format!("Failed to umount {}", src.as_ref().display()))?;
    Ok(())
}
