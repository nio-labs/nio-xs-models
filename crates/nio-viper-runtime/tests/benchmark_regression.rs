use nio_viper_runtime::{
    execute_viper_ast, execute_viper_ast_with_shell, find_default_viper_paths,
    ShellDialect, SpiderSearchHygiene, ViperOutput,
};

#[test]
fn test_viper_runtime_memory_and_early_stopping_regression() {
    let (model_path, tokenizer_path) = match find_default_viper_paths() {
        Some(paths) => paths,
        None => {
            eprintln!("Skipping integration test: Viper model or tokenizer not found on local system");
            return;
        }
    };

    let test_prompts = [
        "Kill whatever process is listening on port 3000",
        "list directory",
        "Delete all stopped docker containers and unused volumes",
    ];

    for (i, prompt) in test_prompts.iter().enumerate() {
        let telemetry = execute_viper_ast(prompt, &model_path, &tokenizer_path, true, 32)
            .expect("Viper AST execution failed");

        eprintln!(
            "Prompt {}: '{}' => tokens={}, rss_init={:.2}MB, rss_working={:.2}MB, hwm_peak={:.2}MB",
            i + 1, prompt, telemetry.tokens, telemetry.rss_init, telemetry.rss_working, telemetry.hwm_peak
        );

        // 1. Working RSS check: working resident memory stays lean (< 100MB in multi-threaded test process)
        assert!(
            telemetry.rss_working < 100.0,
            "Working RSS regression: observed {:.2} MB (must be < 100.0 MB)",
            telemetry.rss_working
        );

        // 2. Early-stopping / token bounding check: must halt within 32 tokens
        assert!(
            telemetry.tokens <= 32,
            "Runaway token generation: produced {} tokens",
            telemetry.tokens
        );

        // 3. Verdict validity
        match telemetry.output {
            ViperOutput::Command(cmd) => {
                assert!(!cmd.is_empty(), "Produced empty command");
            }
            ViperOutput::Alert { message, .. } => {
                assert!(!message.is_empty(), "Produced empty alert");
            }
            ViperOutput::Raw(raw) => {
                assert!(!raw.is_empty(), "Produced empty raw output");
            }
        }
    }
}

#[test]
fn test_viper_powershell_dialect_and_spider_hygiene() {
    let (model_path, tokenizer_path) = match find_default_viper_paths() {
        Some(paths) => paths,
        None => return,
    };

    let telemetry = execute_viper_ast_with_shell(
        "powershell get top 5 processes by memory",
        &model_path,
        &tokenizer_path,
        true,
        32,
        ShellDialect::PowerShell,
    )
    .expect("PowerShell dialect execution failed");

    assert_eq!(telemetry.shell, ShellDialect::PowerShell);
    assert!(telemetry.tokens <= 32);

    // Spider search hygiene unit tests
    let bash_find = SpiderSearchHygiene::apply("find . -type f -name \"*.rs\"", ShellDialect::Bash);
    assert!(bash_find.contains("-not -path '*/target/*'"));
    assert!(bash_find.contains("-not -path '*/.*'"));

    let bash_grep = SpiderSearchHygiene::apply("grep -rn 'SECRET' .", ShellDialect::Bash);
    assert!(bash_grep.contains("-rIn"));
    assert!(bash_grep.contains("--exclude-dir={target,.git,node_modules,dist,.venv}"));

    let pwsh_find = SpiderSearchHygiene::apply("Get-ChildItem -Path . -Recurse", ShellDialect::PowerShell);
    assert!(pwsh_find.contains("-Exclude target,node_modules,.git,.venv"));
}
