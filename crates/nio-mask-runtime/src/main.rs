use std::io::{self, Read};
use nio_mask_runtime::NioMask;

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let mask = NioMask::new();

    let input = if args.len() > 1 {
        args[1..].join(" ")
    } else {
        let mut buffer = String::new();
        io::stdin().read_to_string(&mut buffer)?;
        buffer
    };

    let mut result = mask.sanitize(&input);
    let finish_result = mask.finish();
    if !finish_result.sanitized.is_empty() {
        result.sanitized.push_str(&finish_result.sanitized);
        result.risk_score = result.risk_score.max(finish_result.risk_score);
        result.redacted_count += finish_result.redacted_count;
        let offset = input.len().saturating_sub(finish_result.original.len());
        for mut span in finish_result.spans {
            span.start += offset;
            span.end += offset;
            result.spans.push(span);
        }
        result.is_clean = result.is_clean && finish_result.is_clean;
    }
    println!("{}", serde_json::to_string_pretty(&result)?);

    Ok(())
}
