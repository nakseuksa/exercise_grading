[[四维难度锚点表（Rubric）]]
{
  "type": "object",
  "required": [
    "target_grade_and_subject",
    "optimal_solution_trace",
    "dimensions",
    "diagnostic_tags"
  ],
  "properties": {
    "target_grade_and_subject": {
      "type": "string",
      "description": "评估所锚定的学段与学科基准"
    },
    "optimal_solution_trace": {
      "type": "object",
      "required": ["knowledge_points", "step_by_step_skeleton", "step_count", "key_bottleneck"],
      "properties": {
        "knowledge_points": {
          "type": "array",
          "items": { "type": "string" },
          "description": "最优解法涉及的核心知识点列表"
        },
        "step_by_step_skeleton": {
          "type": "array",
          "items": { "type": "string" },
          "description": "最优解法的核心逻辑推理步骤（仅列逻辑步，合并纯计算）"
        },
        "step_count": {
          "type": "integer",
          "description": "核心逻辑推理步数"
        },
        "key_bottleneck": {
          "type": "string",
          "description": "学生最容易卡壳的思维节点或最易踩中的陷阱描述；若无则填'无明显卡点'"
        }
      }
    },
    "dimensions": {
      "type": "object",
      "required": ["C", "S", "T", "L"],
      "properties": {
        "C": {
          "type": "object",
          "required": ["evidence", "score"],
          "properties": {
            "evidence": { "type": "string", "description": "对照锚点判定思维深度的客观依据" },
            "score": { "type": "integer", "enum": [1, 2, 3, 4] }
          }
        },
        "S": {
          "type": "object",
          "required": ["evidence", "score"],
          "properties": {
            "evidence": { "type": "string", "description": "对照锚点判定推理步数与分支的客观依据" },
            "score": { "type": "integer", "enum": [1, 2, 3] }
          }
        },
        "T": {
          "type": "object",
          "required": ["evidence", "score"],
          "properties": {
            "evidence": { "type": "string", "description": "对照锚点判定信息隐蔽度与陷阱的客观依据" },
            "score": { "type": "integer", "enum": [1, 2, 3] }
          }
        },
        "L": {
          "type": "object",
          "required": ["evidence", "score"],
          "properties": {
            "evidence": { "type": "string", "description": "对照锚点判定运算与审题负荷的客观依据" },
            "score": { "type": "integer", "enum": [1, 2, 3] }
          }
        }
      }
    },
    "diagnostic_tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "2~4个题目特征诊断标签，如'构造辅助线'、'分类讨论'、'高计算负荷'、'定义域陷阱'、'长难句拆解'"
    }
  },
  "additionalProperties": false
}