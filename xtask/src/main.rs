use std::{
    env,
    fs,
    path::PathBuf,
    process::Command,
};

use anyhow::{Context, Result};
use clap::{Parser, ValueEnum};

#[derive(Debug, Clone, Copy, ValueEnum)]
enum Arch {
    #[value(name = "arm64")]
    Arm64,
    #[value(name = "arm")]
    Arm,
    #[value(name = "x86_64")]
    X86_64,
    #[value(name = "riscv64")]
    Riscv64,
}

impl Arch {
    fn target(&self) -> &'static str {
        match self {
            Arch::Arm64 => "aarch64-linux-android",
            Arch::Arm => "armv7-linux-androideabi",
            Arch::X86_64 => "x86_64-linux-android",
            Arch::Riscv64 => "riscv64-linux-android",
        }
    }

    fn android_abi(&self) -> &'static str {
        match self {
            Arch::Arm64 => "arm64-v8a",
            Arch::Arm => "armeabi-v7a",
            Arch::X86_64 => "x86_64",
            Arch::Riscv64 => "riscv64",
        }
    }
    
    fn api_level(&self) -> &'static str {
        match self {
            Arch::Riscv64 => "35",
            _ => "29",
        }
    }
}

#[derive(Parser)]
#[command(name = "xtask")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(clap::Subcommand)]
enum Commands {
    Build {
        #[arg(long, default_value = "false")]
        release: bool,
        #[arg(long, default_value = "arm64")]
        arch: Arch,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Build { release, arch } => {
            build(release, arch)?;
        }
    }
    Ok(())
}

fn build(release: bool, arch: Arch) -> Result<()> {
    let cargo = env::var("CARGO").unwrap_or_else(|_| "cargo".to_string());
    
    if !matches!(arch, Arch::Riscv64) {
        let status = Command::new("rustup")
            .args(["target", "add", arch.target()])
            .status()
            .context("Failed to add rust target")?;

        if !status.success() {
            eprintln!("Warning: Failed to auto-install target {}", arch.target());
        }
    }

    let ndk_home = env::var("ANDROID_NDK_HOME").context("ANDROID_NDK_HOME not set")?;
    let host_os = std::env::consts::OS;
    let host_tag = match host_os {
        "linux" => "linux-x86_64",
        "macos" => "darwin-x86_64",
        "windows" => "windows-x86_64",
        _ => panic!("Unsupported OS: {}", host_os),
    };

    let toolchain_bin = PathBuf::from(ndk_home)
        .join("toolchains/llvm/prebuilt")
        .join(host_tag)
        .join("bin");

    let api = arch.api_level();
    let cc_name = match arch {
        Arch::Arm64 => format!("aarch64-linux-android{}-clang", api),
        Arch::Arm => format!("armv7a-linux-androideabi{}-clang", api),
        Arch::X86_64 => format!("x86_64-linux-android{}-clang", api),
        Arch::Riscv64 => format!("riscv64-linux-android{}-clang", api),
    };

    let cc_path = toolchain_bin.join(&cc_name);
    let ar_path = toolchain_bin.join("llvm-ar");

    println!("Building for ABI: {} (API {})", arch.android_abi(), api);

    let mut cmd = Command::new(&cargo);
    cmd.arg("build")
       .arg("--target").arg(arch.target());

    if matches!(arch, Arch::Riscv64) {
        cmd.arg("-Z").arg("build-std");
    }

    if release {
        cmd.arg("--release");
    }

    let env_target = arch.target().replace('-', "_");
    cmd.env(format!("CC_{}", env_target), &cc_path);
    cmd.env(format!("AR_{}", env_target), &ar_path);
    
    cmd.env("CC", &cc_path);
    cmd.env("AR", &ar_path);

    let status = cmd.status().context("Failed to run cargo build")?;
    if !status.success() {
        anyhow::bail!("Build failed");
    }

    let bin_name = "meta-hybrid"; 
    let profile = if release { "release" } else { "debug" };
    
    let src_path = PathBuf::from("target")
        .join(arch.target())
        .join(profile)
        .join(bin_name);

    let output_dir = PathBuf::from("output/module_files/binaries")
        .join(arch.android_abi());
        
    fs::create_dir_all(&output_dir).context("Failed to create output directory")?;

    let dst_path = output_dir.join(bin_name);

    if src_path.exists() {
        fs::copy(&src_path, &dst_path).context("Failed to copy binary to output")?;
        println!("Artifact copied to: {}", dst_path.display());
    } else {
        anyhow::bail!("Build finished but binary not found at: {}", src_path.display());
    }

    Ok(())
}
