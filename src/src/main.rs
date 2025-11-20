mod magic_mount;
mod utils;

use anyhow::{Context, Result};
use clap::Parser;
use std::path::PathBuf;

const MODULE_DIR_DEFAULT: &str = "/data/adb/modules/";
const MOUNT_SOURCE_DEFAULT: &str = "MaGIcMounT";
const LOG_FILE_DEFAULT: &str = "/data/adb/mm.log";

#[derive(Parser, Debug)]
#[command(name = "magic_mount", version, about = "Magic Mount Metamodule")]
struct Cli {
    /// Module directory path
    #[arg(short = 'm', long = "moduledir", default_value = MODULE_DIR_DEFAULT)]
    moduledir: PathBuf,

    /// Temporary directory path (auto-selected if not specified)
    #[arg(short = 't', long = "tempdir")]
    tempdir: Option<PathBuf>,

    /// Mount source name
    #[arg(short = 's', long = "mountsource", default_value = MOUNT_SOURCE_DEFAULT)]
    mountsource: String,

    /// Log file path
    #[arg(short = 'l', long = "logfile", default_value = LOG_FILE_DEFAULT)]
    logfile: PathBuf,

    /// Enable verbose (debug) logging
    #[arg(short = 'v', long = "verbose")]
    verbose: bool,

    /// Extra partitions, comma-separated, eg: -p mi_ext,my_stock
    #[arg(short = 'p', long = "partitions", value_delimiter = ',')]
    partitions: Vec<String>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    utils::init_logger(&cli.logfile, cli.verbose)?;

    log::info!("Magic Mount Starting");
    log::info!("module dir      : {}", cli.moduledir.display());

    let tempdir = if let Some(temp) = cli.tempdir {
        log::info!("temp dir (user) : {}", temp.display());
        temp
    } else {
        let temp = utils::select_temp_dir()
            .context("failed to select temp dir automatically")?;
        log::info!("temp dir (auto) : {}", temp.display());
        temp
    };

    log::info!("mount source    : {}", cli.mountsource);
    log::info!("log file        : {}", cli.logfile.display());
    log::info!("verbose mode    : {}", cli.verbose);
    if !cli.partitions.is_empty() {
        log::info!("extra partitions: {:?}", cli.partitions);
    }

    utils::ensure_temp_dir(&tempdir)?;

    let result = magic_mount::magic_mount(&tempdir, &cli.moduledir, &cli.mountsource, &cli.partitions);

    utils::cleanup_temp_dir(&tempdir);

    match result {
        Ok(_) => {
            log::info!("Magic Mount Completed Successfully");
            Ok(())
        }
        Err(e) => {
            log::error!("Magic Mount Failed");
            log::error!("error: {:#}", e);
            Err(e)
        }
    }
}
