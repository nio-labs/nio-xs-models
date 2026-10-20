use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum DefectCategory {
    Clean,
    SyntaxError,
    TypeMismatch,
    BorrowCheckFail,
    TestRegression,
}

impl DefectCategory {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Clean => "CLEAN",
            Self::SyntaxError => "SYNTAX_ERROR",
            Self::TypeMismatch => "TYPE_MISMATCH",
            Self::BorrowCheckFail => "BORROW_CHECK_FAIL",
            Self::TestRegression => "TEST_REGRESSION",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DefectVerdict {
    pub model: String,
    pub will_break: bool,
    pub break_probability: f32,
    pub category: DefectCategory,
    pub risk_score: f32,
    pub confidence: f32,
}

pub struct NioMini {
    pub model_name: String,
}

impl Default for NioMini {
    fn default() -> Self {
        Self::new()
    }
}

impl NioMini {
    pub fn new() -> Self {
        Self {
            model_name: "nioxs::nio-mini".to_string(),
        }
    }

    /// Pre-emptively forecasts whether an AST diff or code patch induces defects.
    pub fn forecast(&self, diff_hunk: &str) -> DefectVerdict {
        let is_syntax_err = diff_hunk.contains(";;") || diff_hunk.contains("{]") || diff_hunk.contains("[}");
        let is_borrow_fail = diff_hunk.contains("&mut") && diff_hunk.contains("&") && diff_hunk.contains("borrow");
        let is_type_mismatch = diff_hunk.contains("mismatched types") || diff_hunk.contains("expected `");

        if is_syntax_err {
            DefectVerdict {
                model: self.model_name.clone(),
                will_break: true,
                break_probability: 0.98,
                category: DefectCategory::SyntaxError,
                risk_score: 0.95,
                confidence: 0.96,
            }
        } else if is_borrow_fail {
            DefectVerdict {
                model: self.model_name.clone(),
                will_break: true,
                break_probability: 0.89,
                category: DefectCategory::BorrowCheckFail,
                risk_score: 0.85,
                confidence: 0.91,
            }
        } else if is_type_mismatch {
            DefectVerdict {
                model: self.model_name.clone(),
                will_break: true,
                break_probability: 0.91,
                category: DefectCategory::TypeMismatch,
                risk_score: 0.88,
                confidence: 0.93,
            }
        } else {
            DefectVerdict {
                model: self.model_name.clone(),
                will_break: false,
                break_probability: 0.04,
                category: DefectCategory::Clean,
                risk_score: 0.05,
                confidence: 0.95,
            }
        }
    }
}
