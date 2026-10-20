use std::io::{self, Read};
use nio_mini_runtime::NioMini;

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let mini = NioMini::new();

    let input = if args.len() > 1 {
        args[1..].join(" ")
    } else {
        let mut buffer = String::new();
        io::stdin().read_to_string(&mut buffer)?;
        buffer
    };

    let verdict = mini.forecast(&input);
    println!("{}", serde_json::to_string_pretty(&verdict)?);

    Ok(())
}
