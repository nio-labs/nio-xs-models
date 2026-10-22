pub use nio_ray_runtime::{AstMicroEngine, memory_mb};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CudaStage {
    pub id: String,
    pub model: String,
    pub action: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub file: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cmd: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub task: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub goal: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub scope: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CudaPlan {
    pub task: String,
    pub goal: String,
    pub stages: Vec<CudaStage>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CudaNode {
    pub id: String,
    pub model: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub depends_on: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub action: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub file: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cmd: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub task: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub policy: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CudaDag {
    pub id: String,
    pub task: String,
    pub nodes: Vec<CudaNode>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum CudaOutput {
    Plan(CudaPlan),
    Dag(CudaDag),
    Text(String),
}

fn parse_attribute(tag: &str, attr: &str) -> Option<String> {
    let key1 = format!("{}=\"", attr);
    let key2 = format!("{}='", attr);

    if let Some(idx) = tag.find(&key1) {
        let rest = &tag[idx + key1.len()..];
        let end = rest.find('"').unwrap_or(rest.len());
        Some(rest[..end].to_string())
    } else if let Some(idx) = tag.find(&key2) {
        let rest = &tag[idx + key2.len()..];
        let end = rest.find('\'').unwrap_or(rest.len());
        Some(rest[..end].to_string())
    } else {
        None
    }
}

/// Extract `<cuda_plan ...> ... </cuda_plan>` from conductor output
pub fn extract_cuda_plan(text: &str) -> Option<CudaPlan> {
    let start_tag = "<cuda_plan";
    let end_tag = "</cuda_plan>";

    let start_idx = text.find(start_tag)?;
    let plan_slice = &text[start_idx..];
    let tag_close = plan_slice.find('>')?;
    let header = &plan_slice[..tag_close];

    let task = parse_attribute(header, "task").unwrap_or_else(|| "unnamed-task".to_string());
    let goal = parse_attribute(header, "goal").unwrap_or_else(|| "completion".to_string());

    let content_start = tag_close + 1;
    let content_end = plan_slice.find(end_tag).unwrap_or(plan_slice.len());
    let body = &plan_slice[content_start..content_end];

    let mut stages = Vec::new();

    for line in body.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("<stage") {
            let tag_close = match trimmed.find('>') {
                Some(idx) => idx,
                None => continue,
            };
            let stage_tag = &trimmed[..tag_close];

            let id = parse_attribute(stage_tag, "id").unwrap_or_else(|| (stages.len() + 1).to_string());
            let model = parse_attribute(stage_tag, "model").unwrap_or_else(|| "nio-ray".to_string());
            let action = parse_attribute(stage_tag, "action").unwrap_or_else(|| "execute".to_string());
            let path = parse_attribute(stage_tag, "path");
            let file = parse_attribute(stage_tag, "file");
            let cmd = parse_attribute(stage_tag, "cmd");
            let task_attr = parse_attribute(stage_tag, "task");
            let goal_attr = parse_attribute(stage_tag, "goal");
            let scope = parse_attribute(stage_tag, "scope");

            stages.push(CudaStage {
                id,
                model,
                action,
                path,
                file,
                cmd,
                task: task_attr,
                goal: goal_attr,
                scope,
            });
        }
    }

    Some(CudaPlan { task, goal, stages })
}

/// Extract `<cuda_dag ...> ... </cuda_dag>` from conductor output
pub fn extract_cuda_dag(text: &str) -> Option<CudaDag> {
    let start_tag = "<cuda_dag";
    let end_tag = "</cuda_dag>";

    let start_idx = text.find(start_tag)?;
    let dag_slice = &text[start_idx..];
    let tag_close = dag_slice.find('>')?;
    let header = &dag_slice[..tag_close];

    let id = parse_attribute(header, "id").unwrap_or_else(|| "unnamed-dag".to_string());
    let task = parse_attribute(header, "task").unwrap_or_else(|| "unnamed-task".to_string());

    let content_start = tag_close + 1;
    let content_end = dag_slice.find(end_tag).unwrap_or(dag_slice.len());
    let body = &dag_slice[content_start..content_end];

    let mut nodes = Vec::new();

    for line in body.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("<node") {
            let tag_close = match trimmed.find('>') {
                Some(idx) => idx,
                None => continue,
            };
            let node_tag = &trimmed[..tag_close];

            let id = parse_attribute(node_tag, "id").unwrap_or_else(|| (nodes.len() + 1).to_string());
            let model = parse_attribute(node_tag, "model").unwrap_or_else(|| "nio-ray".to_string());
            let depends_on = parse_attribute(node_tag, "depends_on");
            let action = parse_attribute(node_tag, "action");
            let path = parse_attribute(node_tag, "path");
            let file = parse_attribute(node_tag, "file");
            let cmd = parse_attribute(node_tag, "cmd");
            let task_attr = parse_attribute(node_tag, "task");
            let policy = parse_attribute(node_tag, "policy");

            nodes.push(CudaNode {
                id,
                model,
                depends_on,
                action,
                path,
                file,
                cmd,
                task: task_attr,
                policy,
            });
        }
    }

    Some(CudaDag { id, task, nodes })
}

/// Parse raw conductor text into typed CudaOutput
pub fn parse_cuda_output(text: &str) -> CudaOutput {
    if let Some(plan) = extract_cuda_plan(text) {
        if !plan.stages.is_empty() {
            return CudaOutput::Plan(plan);
        }
    }
    if let Some(dag) = extract_cuda_dag(text) {
        if !dag.nodes.is_empty() {
            return CudaOutput::Dag(dag);
        }
    }
    CudaOutput::Text(text.trim().to_string())
}

/// Format task into ChatML prompt for NioCuda
pub fn format_cuda_prompt(task_desc: &str, use_dag: bool) -> String {
    let mode_hint = if use_dag {
        "Schedule an asynchronous DAG coordination structure using <cuda_dag> and <node> specifications."
    } else {
        "Generate a sequential tactical coordination plan using <cuda_plan> and <stage> specifications."
    };

    let system_prompt = format!(
        "You are NioCuda, the tactical swarm conductor and air-traffic controller for NioXS. \
         You synthesize developer tasks into atomic, deterministic coordination plans across the Nio fleet: \
         nio-nano (AST navigation & triage), nio-ray (keystroke code generation), \
         nio-mini (defect & lint audit), nio-viper (terminal & test execution), \
         and nio-micro (policy verdict & approval). {mode_hint}"
    );

    format!(
        "<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\nCoordinate the swarm to execute this task: {task_desc}<|im_end|>\n<|im_start|>assistant\n"
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_cuda_plan() {
        let sample = r#"
Tactical plan initialized for task 'Fix memory leak'.

<cuda_plan task="Fix memory leak" goal="Deterministic zero-defect completion">
  <stage id="1" model="nio-nano" action="symbol_triage" path="crates/events/src/bus.rs" goal="Index AST symbols" />
  <stage id="2" model="nio-ray" action="keystroke_code" file="crates/events/src/bus.rs" task="Fix leak" />
  <stage id="3" model="nio-mini" action="defect_audit" file="crates/events/src/bus.rs" target="AST syntax" />
  <stage id="4" model="nio-viper" action="terminal_verify" cmd="cargo test -p events" />
  <stage id="5" model="nio-micro" action="policy_verdict" scope="Diff approval" />
</cuda_plan>
"#;

        let plan = extract_cuda_plan(sample).expect("Should parse plan");
        assert_eq!(plan.task, "Fix memory leak");
        assert_eq!(plan.goal, "Deterministic zero-defect completion");
        assert_eq!(plan.stages.len(), 5);
        assert_eq!(plan.stages[0].model, "nio-nano");
        assert_eq!(plan.stages[1].model, "nio-ray");
        assert_eq!(plan.stages[2].model, "nio-mini");
        assert_eq!(plan.stages[3].model, "nio-viper");
        assert_eq!(plan.stages[4].model, "nio-micro");
        assert_eq!(plan.stages[3].cmd.as_deref(), Some("cargo test -p events"));
    }

    #[test]
    fn test_extract_cuda_dag() {
        let sample = r#"
Conductor DAG scheduled for 'Upgrade hashing'.

<cuda_dag id="task-auth-0" task="Upgrade hashing">
  <node id="triage" model="nio-nano" action="symbol_triage" path="crates/auth/src/hash.rs" />
  <node id="codegen" model="nio-ray" depends_on="triage" file="crates/auth/src/hash.rs" task="Upgrade hashing" />
  <node id="audit" model="nio-mini" depends_on="codegen" file="crates/auth/src/hash.rs" />
  <node id="verify" model="nio-viper" depends_on="audit" cmd="cargo test -p auth" />
  <node id="verdict" model="nio-micro" depends_on="verify" policy="security_audit_pass" />
</cuda_dag>
"#;

        let dag = extract_cuda_dag(sample).expect("Should parse DAG");
        assert_eq!(dag.id, "task-auth-0");
        assert_eq!(dag.nodes.len(), 5);
        assert_eq!(dag.nodes[1].depends_on.as_deref(), Some("triage"));
        assert_eq!(dag.nodes[4].policy.as_deref(), Some("security_audit_pass"));
    }
}
