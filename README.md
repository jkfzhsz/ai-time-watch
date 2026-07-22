# AI Time Watch

**为 AI Agent 提供"手表"能力 —— 时序感知与自动调度技能。**

每次对话中，当用户语句出现时间概念时，`ai-time-watch` 自动检测并判定时态（过去/现在/将来），对将来事件执行二次分流（预测型/定时型），并在需要时自动调用 `Schedule` 工具创建 cron 定时任务。

## 核心能力

```
用户输入 → 时间信号检测 → 三时态判定 → 将来事件二次分流
                                              ├── 预测型 → 继续推理
                                              └── 定时型 → Schedule 定时任务
```

| 时态 | 行为 |
|------|------|
| **过去** | 判定后继续推理 |
| **现在** | 判定后继续推理 |
| **将来** | 硬约束：不搜索未来 → 二次判定（预测 / 定时） |

## 安装

将 `SKILL.md` 放入项目的 `.trae/skills/ai-time-watch/` 目录：

```bash
mkdir -p .trae/skills/ai-time-watch
cp SKILL.md .trae/skills/ai-time-watch/SKILL.md
```

TRAE 会在下次对话中自动加载该技能。

## 依赖

- **TRAE** 运行时环境
- **Schedule 工具**（用于创建 cron 定时任务）
- 系统时间可获取（`Today's date` 提示或 `Get-Date` 命令）

## 触发条件

当用户输入中出现以下任意时间概念时自动触发：

- **绝对时间**："昨天"、"明天"、"下周一"、"2024年"
- **相对时间**："刚才"、"过几天"、"尽快"
- **进行中**："现在"、"当前"、"正在"、"今天"
- **周期性**："每天"、"每周"、"每月"、"每个工作日"

## 输出格式

```json
{
  "tense": "past | present | future",
  "time_expressions": ["提取的时间表述"],
  "action": "reason | predict | schedule",
  "reference_precision": "datetime | date_only",
  "precision_note": null,
  "schedule_suggestion": {
    "should_schedule": true,
    "cron_expression": "0 9 * * 1",
    "task_description": "任务描述",
    "reasoning": "判定理由"
  }
}
```

## 设计原则

- **不搜索未来**：将来事件绝不发起 WebSearch/WebFetch
- **保守策略**：模糊时间表述默认倾向于将来-定时型
- **精度降级**：支持 datetime → date_only 两级精度兜底
- **降级容错**：Schedule 不可用时仅输出判定，不中断流程

## 验证

```bash
# 运行 16 项验证测试
python tests/test_ai_time_watch.py

# 运行 10 维度质量评测
python tests/eval_ai_time_watch.py
```

## 质量评级

**A+ 优秀**（99/100）

| 维度 | 得分 |
|------|------|
| Frontmatter 质量 | 10/10 |
| 触发条件清晰度 | 10/10 |
| 核心流程完整性 | 15/15 |
| 指令可操作性 | 15/15 |
| 示例质量 | 10/10 |
| 异常与降级处理 | 10/10 |
| 简洁性与可读性 | 9/10 |
| Schedule 集成深度 | 10/10 |
| 跨场景适应性 | 5/5 |
| 安全与约束 | 5/5 |

## 项目结构

```
ai-time-watch/
├── SKILL.md              # 技能指令文件
├── README.md
├── docs/
│   └── spec.md           # 设计 Spec 文档
├── tests/
│   ├── test_ai_time_watch.py  # 16 项验证测试
│   └── eval_ai_time_watch.py  # 10 维度质量评测
└── .github/
    └── workflows/
        └── test.yml       # CI 自动测试
```

## 许可证

MIT License