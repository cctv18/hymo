mod config;
mod defs;
mod engine;
mod logger; // New module
#[path = "magic_mount/mod.rs"]
mod magic_mount;
mod overlay_mount;
mod scanner;
mod utils;

use std::path::{Path, PathBuf};

use anyhow::Result;
use clap::{Parser, Subcommand};
use config::{Config, CONFIG_FILE_DEFAULT};

#[derive(Parser, Debug)]
#[command(name = "meta-hybrid", version, about = "Hybrid Mount Metamodule")]
struct Cli {
    #[arg(short = 'c', long = "config")]
    config: Option<PathBuf>,
    #[arg(short = 'm', long = "moduledir")]
    moduledir: Option<PathBuf>,
    #[arg(short = 't', long = "tempdir")]
    tempdir: Option<PathBuf>,
    #[arg(short = 's', long = "mountsource")]
    mountsource: Option<String>,
    #[arg(short = 'v', long = "verbose")]
    verbose: bool,
    #[arg(short = 'p', long = "partitions", value_delimiter = ',')]
    partitions: Vec<String>,
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
enum Commands {
    GenConfig {
        #[arg(short = 'o', long = "output", default_value = CONFIG_FILE_DEFAULT)]
        output: PathBuf,
    },
    ShowConfig,
}

fn load_config(cli: &Cli) -> Result<Config> {
    if let Some(config_path) = &cli.config {
        return Config::from_file(config_path);
    }

    match Config::load_default() {
        Ok(config) => Ok(config),
        Err(e) => {
            if Path::new(CONFIG_FILE_DEFAULT).exists() {
                eprintln!("Error loading config file: {:#}", e);
                eprintln!("Falling back to default configuration.");
            }
            Ok(Config::default())
        }
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    if let Some(command) = &cli.command {
        match command {
            Commands::GenConfig { output } => {
                let config = Config::default();
                config.save_to_file(output)?;
                println!("Config generated at {}", output.display());
                return Ok(());
            }
            Commands::ShowConfig => {
                let config = load_config(&cli)?;
                println!("{:#?}", config);
                return Ok(());
            }
        }
    }

    let mut config = load_config(&cli)?;
    config.merge_with_cli(
        cli.moduledir,
        cli.tempdir,
        cli.mountsource,
        cli.verbose,
        cli.partitions,
    );

    // 2. Init Tracing Logger
    // Uses the new logger module
    logger::init(config.verbose, Path::new(defs::DAEMON_LOG_FILE))?;

    if config.verbose {
        tracing::debug!("Verbose logging enabled.");
        tracing::debug!("Loaded configuration: {:#?}", config);
    }

    tracing::info!("Hybrid Mount Starting...");

    // 3. Scan
    let active_modules = scanner::scan_active_modules()?;
    tracing::info!("Found {} enabled modules (Standard + Mnt)", active_modules.len());

    // 4. Engine Run
    engine::run(active_modules, &config)?;

    Ok(())
}
