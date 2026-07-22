# AI Time Watch（AI 时序管理技能）Spec

> Status: ALIGNED
> Author: zongxin
> Last updated: 2026-07-22

## Background

在 Agent 多轮对话中，用户语句经常包含时间概念（"明天"、"下周一"、"去年"、"刚才说的"）。Agent 需要在没有人类持续提醒的情况下，自主判断用户意图发生在过去、现在还是将来，并根据不同时态采取不同行动。本 Skill 为 Agent 提供一块"手表"，在每轮对话中强制检测时间信号，自动分流处理。

## In scope

- 检测用户输入中的时间概念（显式时间词、隐式时间意图）
- 判定事件时态：过去、现在（含当前进行中）、将来
- 过去/现在事件：直接输出判定结果，允许 Agent 继续推理
- 将来事件：**不搜索**未来信息，执行二次判定分流
- 二次判定（将来事件）：
  - 预测型：用户需要基于现有数据预测未来 → 继续推理
  - 定时型：用户需要在将来的某个时间点获取准确结论 → 调用 `Schedule` 工具创建定时任务
- 输出结构化判定结果，供 Agent 后续流程消费

## Out of scope

- 不实现时间表达式的 NLP 解析器（依赖 Agent 自身 LLM 理解能力）
- 不修改 `Schedule` 工具本身
- 不处理跨时区转换（默认使用当前系统时区 `Asia/Shanghai`）
- 不存储历史时间判定记录

## Assumptions

- Agent 运行环境已安装 `Schedule` 工具，支持 cron 定时任务
- 当前系统时间始终可用（`Today's date` 在 system prompt 中提供）
- 用户的时区为 `Asia/Shanghai`
- Skill 以指令文件（SKILL.md）形式存在，由 TRAE 的 Skill 系统加载

## Solution

### 核心流程

```
用户输入
    │
    ▼
┌─────────────────────┐
│ 1. 检测时间概念       │
│ 扫描用户输入，提取    │
│ 所有时间相关表述      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 2. 时态判定           │
│ 过去 / 现在 / 将来    │
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
  过去/现在    将来
    │         │
    ▼         ▼
  继续推理  ┌─────────────────────┐
           │ 3. 二次判定（将来）   │
           │ 预测型 / 定时型       │
           └────────┬────────────┘
                    │
            ┌───────┴───────┐
            ▼               ▼
          预测型           定时型
            │               │
            ▼               ▼
       基于现有数据     调用 Schedule
       继续推理         创建定时任务
```

### 时态判定规则

| 时态 | 判定标准 | 示例 |
|---|---|---|
| 过去 | 时间点 < 当前时间 | "昨天"、"上周"、"2024年"、"刚才" |
| 现在 | 时间点 ≈ 当前时间（含进行中） | "现在"、"当前"、"正在"、"今天" |
| 将来 | 时间点 > 当前时间 | "明天"、"下周"、"下个月"、"明年" |

**硬约束**: 对于将来事件，**绝对不发起 WebSearch 或 WebFetch 获取未来信息**（因为不存在）。

### 二次判定规则（将来事件）

| 类型 | 判定标准 | 行动 |
|---|---|---|
| 预测型 | 用户询问基于现有数据的趋势/预测 | 输出判定，允许 Agent 继续推理（基于过去/现在数据） |
| 定时型 | 用户需要在特定将来时间获取准确结论 | 调用 `Schedule` 创建定时任务 |

**预测型 vs 定时型 区分示例**:

| 用户输入 | 类型 | 原因 |
|---|---|---|
| "根据最近三个月的销售数据，预测下季度趋势" | 预测型 | 需要基于现有数据做推理 |
| "下周一早上9点帮我整理上周的销售周报" | 定时型 | 需要在将来时间点执行具体任务 |
| "明年这个行业会怎么样？" | 预测型 | 基于趋势推演 |
| "每天下午5点帮我拉取当日收盘数据" | 定时型 | 具体的重复性定时任务 |
| "如果按这个增速，年底能到多少用户？" | 预测型 | 基于现有增速做数学推算 |

### 输出格式

Skill 输出一个结构化判定结果：

```json
{
  "tense": "past | present | future",
  "time_expressions": ["提取的时间表述列表"],
  "action": "reason | predict | schedule",
  "schedule_suggestion": {
    "should_schedule": true/false,
    "cron_expression": "0 9 * * 1",
    "task_description": "任务描述",
    "reasoning": "判定理由"
  }
}
```

## Edge cases & risks

| Category | Notes |
|---|---|
| 边界条件 | 用户输入不含任何时间概念 → 不触发本 Skill，静默跳过 |
| 边界条件 | 时间表述模糊（"过几天"、"尽快"）→ 默认视为将来-预测型，不做定时调度 |
| 边界条件 | 多个时间概念混在同一输入 → 逐个判定，分别输出 |
| 失败模式 | Schedule 工具不可用 → 降级为仅输出判定结果，标注"定时任务创建失败：Schedule 工具不可用" |
| 失败模式 | cron 表达式无法表达用户需求（如"第三周周五"）→ 告知用户限制，建议最接近的替代方案 |
| 风险 | 误判时态导致本该定时的任务被当作预测 → 在 Skill 指令中设置保守策略：模糊时倾向于将来-定时型 |

## Acceptance criteria

- AC-1 输入含"昨天" → 输出 `tense: "past"`, `action: "reason"`
- AC-2 输入含"现在"或"今天" → 输出 `tense: "present"`, `action: "reason"`
- AC-3 输入含"明年市场规模会多大" → 输出 `tense: "future"`, `action: "predict"`，且不触发任何 WebSearch
- AC-4 输入含"每天下午5点帮我拉数据" → 输出 `tense: "future"`, `action: "schedule"`, `schedule_suggestion.should_schedule: true`
- AC-5 输入不含任何时间概念 → Skill 不触发，Agent 正常继续
- AC-6 输入含"下周一早上9点整理周报" → 输出 `action: "schedule"`，cron 表达式正确对应周一 9:00
- AC-7 输入含多个时间概念（"回顾上周，规划下周"）→ 分别判定，输出两个判定结果

## Core entities (ontology)

| Entity | Type | Key fields | Relationship |
|---|---|---|---|
| TimeSignal | 时间信号 | expression, tense, parsed_time | 从用户输入中提取 |
| TenseVerdict | 时态判定 | tense (past/present/future), confidence | 一个 TimeSignal 对应一个 |
| FutureAction | 将来行动 | type (predict/schedule), cron?, task_description | 仅当 tense=future 时产生 |

## Open questions

- 无

## Interview metadata

- Mode: --quick
- Waves: 1
- Final ambiguity: 17.2%
- Status: PASSED

### Clarity breakdown

| Dimension | Score | Weight | Weighted |
|---|---|---|---|
| Goal | 0.9 | 0.43 | 0.387 |
| Scope | 0.85 | 0.28 | 0.238 |
| AC | 0.7 | 0.29 | 0.203 |