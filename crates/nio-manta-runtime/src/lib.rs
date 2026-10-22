pub use nio_ray_runtime::{AstMicroEngine, memory_mb};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MantaStep {
    pub id: String,
    pub priority: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MantaRisk {
    pub level: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MantaPlan {
    pub id: String,
    pub steps: Vec<MantaStep>,
    pub risks: Vec<MantaRisk>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum MantaOutput {
    Plan(MantaPlan),
    Dialogue(String),
}

/// Extract `<manta_plan id='...'>...</manta_plan>` structured blocks from model output
pub fn extract_manta_plan(text: &str) -> Option<MantaPlan> {
    let start_tag = "<manta_plan";
    let end_tag = "</manta_plan>";

    let start_idx = text.find(start_tag)?;
    let plan_slice = &text[start_idx..];
    let tag_close = plan_slice.find('>')?;
    let header = &plan_slice[..tag_close];

    let id = if let Some(id_idx) = header.find("id=\"") {
        let rest = &header[id_idx + 4..];
        let end = rest.find('"').unwrap_or(rest.len());
        rest[..end].to_string()
    } else if let Some(id_idx) = header.find("id='") {
        let rest = &header[id_idx + 4..];
        let end = rest.find('\'').unwrap_or(rest.len());
        rest[..end].to_string()
    } else {
        "unnamed-plan".to_string()
    };

    let content_start = tag_close + 1;
    let content_end = plan_slice.find(end_tag).unwrap_or(plan_slice.len());
    let body = &plan_slice[content_start..content_end];

    let mut steps = Vec::new();
    let mut risks = Vec::new();

    // Parse steps
    for line in body.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("<manta_step") {
            let step_tag_close = match trimmed.find('>') {
                Some(idx) => idx,
                None => continue,
            };
            let step_header = &trimmed[..step_tag_close];

            let step_id = if let Some(id_idx) = step_header.find("id=\"") {
                let rest = &step_header[id_idx + 4..];
                let end = rest.find('"').unwrap_or(rest.len());
                rest[..end].to_string()
            } else {
                (steps.len() + 1).to_string()
            };

            let priority = if let Some(p_idx) = step_header.find("priority=\"") {
                let rest = &step_header[p_idx + 10..];
                let end = rest.find('"').unwrap_or(rest.len());
                rest[..end].to_string()
            } else {
                "medium".to_string()
            };

            let step_content = &trimmed[step_tag_close + 1..];
            let step_text = if let Some(close_idx) = step_content.find("</manta_step>") {
                step_content[..close_idx].trim().to_string()
            } else {
                step_content.trim().to_string()
            };

            steps.push(MantaStep {
                id: step_id,
                priority,
                description: step_text,
            });
        } else if trimmed.starts_with("<manta_risk") {
            let risk_tag_close = match trimmed.find('>') {
                Some(idx) => idx,
                None => continue,
            };
            let risk_header = &trimmed[..risk_tag_close];

            let level = if let Some(l_idx) = risk_header.find("level=\"") {
                let rest = &risk_header[l_idx + 7..];
                let end = rest.find('"').unwrap_or(rest.len());
                rest[..end].to_string()
            } else {
                "warning".to_string()
            };

            let risk_content = &trimmed[risk_tag_close + 1..];
            let risk_text = if let Some(close_idx) = risk_content.find("</manta_risk>") {
                risk_content[..close_idx].trim().to_string()
            } else {
                risk_content.trim().to_string()
            };

            risks.push(MantaRisk {
                level,
                message: risk_text,
            });
        }
    }

    Some(MantaPlan { id, steps, risks })
}

/// Parse raw model output into structured MantaOutput
pub fn parse_manta_output(text: &str) -> MantaOutput {
    if let Some(plan) = extract_manta_plan(text) {
        if !plan.steps.is_empty() {
            return MantaOutput::Plan(plan);
        }
    }
    MantaOutput::Dialogue(text.trim().to_string())
}

/// Format user query into standard ChatML format with Manta's mentor persona
pub fn format_manta_prompt(user_query: &str, is_planning: bool) -> String {
    let system_prompt = if is_planning {
        "You are NioManta, the architectural planning companion for NioGuru and NioXS. \
         Decompose technical tasks into structured implementation roadmaps using <manta_plan>, \
         <manta_step>, and <manta_risk> tags."
    } else {
        "You are NioManta, the warm, intelligent developer companion for NioGuru and NioXS. \
         You provide crystal-clear technical explanations, debugging advice, and concise code snippets with zero conversational fluff."
    };

    format!(
        "<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_query}<|im_end|>\n<|im_start|>assistant\n"
    )
}
