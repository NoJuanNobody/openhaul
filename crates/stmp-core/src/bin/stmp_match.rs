//! Runs one STMP matching pass.
//!
//! Reads a `MatchInput` JSON document on stdin and writes a `MatchOutput` JSON
//! document on stdout. Exits non-zero with a message on stderr if the input is
//! unreadable or malformed.

use std::io::{self, Read, Write};
use std::process::ExitCode;

use stmp_core::{run_matching, MatchInput};

fn main() -> ExitCode {
    let mut raw = String::new();
    if let Err(err) = io::stdin().read_to_string(&mut raw) {
        eprintln!("stmp_match: failed to read stdin: {err}");
        return ExitCode::FAILURE;
    }

    let input: MatchInput = match serde_json::from_str(&raw) {
        Ok(input) => input,
        Err(err) => {
            eprintln!("stmp_match: invalid input JSON: {err}");
            return ExitCode::FAILURE;
        }
    };

    let output = run_matching(input);
    let text = match serde_json::to_string(&output) {
        Ok(text) => text,
        Err(err) => {
            eprintln!("stmp_match: failed to serialize output: {err}");
            return ExitCode::FAILURE;
        }
    };

    let mut stdout = io::stdout().lock();
    if writeln!(stdout, "{text}").is_err() {
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}
