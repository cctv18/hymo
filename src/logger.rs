use std::path::Path;
use anyhow::Result;
use tracing_subscriber::fmt::format::Writer;
use tracing_subscriber::fmt::time::FormatTime;
use tracing_subscriber::{fmt, EnvFilter, Layer};
use tracing_subscriber::prelude::*;

// Custom timer is not strictly needed if we don't log time in the file 
// (WebUI doesn't seem to parse time, just Level/Target/Msg)
// But standard logs usually have it. The original FileLogger didn't have a timestamp.
// Original format: "[{}] [{}] {}" -> [LEVEL] [TARGET] MESSAGE

struct SimpleFormatter;

impl<S, N> fmt::FormatEvent<S, N> for SimpleFormatter
where
    S: tracing::Subscriber + for<'a> tracing_subscriber::registry::LookupSpan<'a>,
    N: for<'a> fmt::FormatFields<'a> + 'static,
{
    fn format_event(
        &self,
        ctx: &fmt::FmtContext<'_, S, N>,
        mut writer: Writer<'_>,
        event: &tracing::Event<'_>,
    ) -> std::fmt::Result {
        let metadata = event.metadata();
        let level = metadata.level();
        let target = metadata.target();

        // Match original format: [INFO] [target] message
        write!(writer, "[{}] [{}] ", level, target)?;

        // Write the actual message
        ctx.format_fields(writer.by_ref(), event)?;
        writeln!(writer)
    }
}

pub fn init(verbose: bool, log_path: &Path) -> Result<()> {
    let level = if verbose { "debug" } else { "info" };
    
    // 1. File Layer (Non-blocking)
    // We split path into directory and filename for tracing_appender
    let log_dir = log_path.parent().unwrap_or_else(|| Path::new("/data/adb/meta-hybrid"));
    let log_file_name = log_path.file_name().unwrap_or_else(|| std::ffi::OsStr::new("daemon.log"));

    let file_appender = tracing_appender::rolling::never(log_dir, log_file_name);
    let (non_blocking, _guard) = tracing_appender::non_blocking(file_appender);
    let file_appender = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(log_path)?;

    let file_layer = fmt::layer()
        .with_writer(file_appender)
        .with_ansi(false)
        .event_format(SimpleFormatter);

    // 2. Filter Layer
    let filter = EnvFilter::new(level);

    // 3. Init
    tracing_subscriber::registry()
        .with(filter)
        .with(file_layer)
        .init();

    // Redirect standard `log` crate macros to `tracing`
    // This ensures dependencies using `log::info!` still work
    tracing_log::LogTracer::init()?;

    Ok(())
}
