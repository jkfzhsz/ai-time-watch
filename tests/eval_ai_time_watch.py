"""
AI Time Watch Skill — 多维度质量评测
评测标准：基于 Skill Creator 规范和指令型 Skill 最佳实践
"""
import os
import re
import json

SKILL_PATH = r"d:\Trae\.trae\skills\ai-time-watch\SKILL.md"


def load_skill():
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        return f.read()


class EvalResult:
    def __init__(self):
        self.dimensions = {}
        self.total_score = 0
        self.max_score = 0

    def add(self, name, score, max_score, note=""):
        self.dimensions[name] = {"score": score, "max": max_score, "note": note}
        self.total_score += score
        self.max_score += max_score

    def percentage(self):
        return round(self.total_score / self.max_score * 100, 1) if self.max_score > 0 else 0

    def grade(self):
        p = self.percentage()
        if p >= 90: return "A+ 优秀"
        if p >= 80: return "A 良好"
        if p >= 70: return "B 合格"
        if p >= 60: return "C 待改进"
        return "D 不合格"


def evaluate():
    content = load_skill()
    lines = content.split("\n")
    result = EvalResult()

    # ================================================================
    # 维度 1: Frontmatter 质量 (10分)
    # ================================================================
    score = 0
    notes = []
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        name_m = re.search(r'name:\s*"([^"]+)"', fm)
        desc_m = re.search(r'description:\s*"([^"]+)"', fm)

        if name_m and name_m.group(1) == "ai-time-watch":
            score += 2
        else:
            notes.append("name 字段缺失或不匹配")

        if desc_m:
            desc = desc_m.group(1)
            desc_len = len(desc)
            if 20 <= desc_len <= 200:
                score += 3
            elif desc_len < 20:
                score += 1
                notes.append(f"description 过短 ({desc_len} chars)")
            else:
                score += 2
                notes.append(f"description 超长 ({desc_len} chars)")

            # description 是否包含触发条件
            if any(kw in desc for kw in ["触发", "当", "when", "invoke", "调用"]):
                score += 3
            else:
                notes.append("description 缺少触发条件说明")
        else:
            notes.append("description 字段缺失")

        # frontmatter 无多余字段
        extra_fields = [l for l in fm.split("\n") if l.strip() and not l.startswith("name:") and not l.startswith("description:")]
        if not extra_fields:
            score += 2
        else:
            notes.append(f"frontmatter 含多余字段: {extra_fields}")
    else:
        notes.append("frontmatter 格式错误")

    result.add("Frontmatter 质量", score, 10, "; ".join(notes) if notes else "完整规范")

    # ================================================================
    # 维度 2: 触发条件清晰度 (10分)
    # ================================================================
    score = 0
    notes = []

    trigger_phrases = ["时间概念", "时间信号", "时间表述", "触发", "强制触发"]
    hits = sum(1 for t in trigger_phrases if t in content)
    if hits >= 3:
        score += 4
    elif hits >= 1:
        score += 2
    else:
        notes.append("触发条件表述不够明确")

    # 是否有"不触发"规则
    if "不触发" in content or "静默跳过" in content or "跳过" in content:
        score += 3
    else:
        notes.append("缺少不触发/跳过规则")

    # 时间概念分类是否完整
    categories = ["绝对时间", "相对时间", "进行中", "周期性"]
    cat_hits = sum(1 for c in categories if c in content)
    score += min(cat_hits, 3)

    result.add("触发条件清晰度", score, 10, "; ".join(notes) if notes else f"触发条件明确，{cat_hits}/4 类时间概念覆盖")

    # ================================================================
    # 维度 3: 核心流程完整性 (15分)
    # ================================================================
    score = 0
    notes = []

    # 三时态判定
    if all(kw in content for kw in ["过去", "现在", "将来"]):
        score += 4
    else:
        notes.append("三时态判定不完整")

    # 二次判定
    if "预测" in content and "定时" in content:
        score += 3
    else:
        notes.append("缺少二次判定（预测/定时）")

    # 未来不搜索硬约束
    if "不搜索" in content or "不发起" in content or "绝对不发起" in content:
        score += 3
    else:
        notes.append("缺少'不搜索未来'硬约束")

    # Schedule 集成
    if "Schedule" in content:
        score += 3
    else:
        notes.append("缺少 Schedule 工具集成")

    # 多时间概念处理
    if "多时间" in content or "多个时间" in content:
        score += 2
    else:
        notes.append("缺少多时间概念处理规则")

    result.add("核心流程完整性", score, 15, "; ".join(notes) if notes else "完整覆盖：三时态→二次判定→Schedule")

    # ================================================================
    # 维度 4: 指令可操作性 (15分)
    # ================================================================
    score = 0
    notes = []

    # 是否有明确的行动指令（非纯描述性）
    action_verbs = ["调用", "输出", "判定", "提取", "创建", "标注", "告知"]
    verb_hits = sum(1 for v in action_verbs if v in content)
    score += min(verb_hits, 5)

    # 是否有结构化输出格式
    if "json" in content.lower():
        score += 3
    else:
        notes.append("缺少结构化 JSON 输出格式")

    # 字段是否完整定义
    if "tense" in content and "action" in content and "time_expressions" in content:
        score += 3
    else:
        notes.append("输出字段定义不完整")

    # 判定标准是否具体（有数值/对比基准）
    if "当前时间" in content or "Today's date" in content:
        score += 2
    else:
        notes.append("缺少时间判定基准")

    # 是否有决策树/流程图或明确的 if-else 逻辑
    if "→" in content or "如果" in content or "若" in content:
        score += 2
    else:
        notes.append("缺少明确的决策逻辑")

    result.add("指令可操作性", score, 15, "; ".join(notes) if notes else "指令清晰，Agent 可直接执行")

    # ================================================================
    # 维度 5: 示例质量 (10分)
    # ================================================================
    score = 0
    notes = []

    # 示例数量
    example_count = content.count('"> 用户：')
    if example_count >= 5:
        score += 4
    elif example_count >= 3:
        score += 3
    elif example_count >= 1:
        score += 1
    else:
        notes.append("缺少完整示例")

    # 示例是否覆盖所有时态
    has_past_example = "past" in content and "上周" in content
    has_present_example = "present" in content and "现在" in content
    has_future_predict = "predict" in content and "明年" in content
    has_future_schedule = "schedule" in content and "每天" in content
    has_multi = "多时间" in content or "上周" in content and "下周" in content

    coverage = sum([has_past_example, has_present_example, has_future_predict, has_future_schedule, has_multi])
    score += coverage

    if coverage < 5:
        missing = []
        if not has_past_example: missing.append("过去时态示例")
        if not has_present_example: missing.append("现在时态示例")
        if not has_future_predict: missing.append("将来-预测型示例")
        if not has_future_schedule: missing.append("将来-定时型示例")
        if not has_multi: missing.append("多时间概念示例")
        notes.append(f"缺少: {', '.join(missing)}")

    # 示例是否包含 JSON 输出
    json_blocks = content.count("```json")
    if json_blocks >= 4:
        score += 1
    else:
        notes.append("JSON 示例不足")

    result.add("示例质量", score, 10, "; ".join(notes) if notes else f"5 类场景全覆盖，{json_blocks} 个 JSON 示例")

    # ================================================================
    # 维度 6: 异常与降级处理 (10分)
    # ================================================================
    score = 0
    notes = []

    # 降级策略
    if "降级" in content or "异常" in content:
        score += 3
    else:
        notes.append("缺少降级/异常处理策略")

    # Schedule 不可用
    if "不可用" in content or "unavailable" in content.lower():
        score += 2

    # cron 限制
    if "cron" in content.lower() and ("限制" in content or "无法" in content or "不支持" in content):
        score += 2

    # 时区处理
    if "时区" in content or "timezone" in content.lower():
        score += 2

    # 模糊时间策略
    if "模糊" in content:
        score += 1
    else:
        notes.append("缺少模糊时间处理策略")

    result.add("异常与降级处理", score, 10, "; ".join(notes) if notes else "降级策略完整")

    # ================================================================
    # 维度 7: 简洁性与可读性 (10分)
    # ================================================================
    score = 0
    notes = []

    total_lines = len(lines)
    if 30 <= total_lines <= 250:
        score += 4
    elif total_lines < 30:
        score += 1
        notes.append(f"过短 ({total_lines} 行)")
    else:
        score += 2
        notes.append(f"偏长 ({total_lines} 行)，但内容完整")

    # 章节结构
    sections = [l.strip() for l in lines if l.startswith("## ")]
    if 3 <= len(sections) <= 10:
        score += 3
    elif len(sections) > 10:
        score += 2
        notes.append(f"章节偏多 ({len(sections)} 个)")
    else:
        score += 1
        notes.append(f"章节偏少 ({len(sections)} 个)")

    # 表格/列表使用
    has_table = content.count("|---|") >= 2
    has_list = content.count("\n- ") >= 5
    if has_table and has_list:
        score += 3
    elif has_table or has_list:
        score += 2
    else:
        notes.append("缺少结构化呈现（表格/列表）")

    result.add("简洁性与可读性", score, 10, "; ".join(notes) if notes else f"{total_lines}行, {len(sections)}章节, 结构清晰")

    # ================================================================
    # 维度 8: 与 Schedule 工具的集成深度 (10分)
    # ================================================================
    score = 0
    notes = []

    if "Schedule" in content:
        score += 2  # 提及 Schedule

        if "cron" in content.lower():
            score += 3  # 包含 cron 表达式

        if "should_schedule" in content.lower():
            score += 2  # 有明确的调度开关

        if "task_description" in content.lower():
            score += 2  # 有任务描述字段

        if "cron_expression" in content.lower():
            score += 1  # 有 cron 表达式字段
    else:
        notes.append("未集成 Schedule 工具")

    result.add("Schedule 集成深度", score, 10, "; ".join(notes) if notes else "cron + 任务描述 + 调度开关 完整")

    # ================================================================
    # 维度 9: 跨场景适应性 (5分)
    # ================================================================
    score = 0
    notes = []

    # 是否覆盖业务/金融/日常等多场景
    scenarios = ["销售", "股市", "会议", "项目", "市场", "收盘"]
    scene_hits = sum(1 for s in scenarios if s in content)
    score += min(scene_hits, 3)

    # 是否同时支持中文和英文时间表达
    if "today" in content.lower() or "yesterday" in content.lower() or "tomorrow" in content.lower():
        score += 1

    # 是否支持周期性时间
    if "每天" in content or "每周" in content or "每月" in content:
        score += 1
    else:
        notes.append("周期时间覆盖不足")

    result.add("跨场景适应性", score, 5, "; ".join(notes) if notes else f"{scene_hits} 类场景覆盖")

    # ================================================================
    # 维度 10: 安全与约束 (5分)
    # ================================================================
    score = 0
    notes = []

    # 不搜索未来
    if "不搜索" in content or "不发起" in content or "绝对不发起" in content:
        score += 2

    # 保守策略
    if "保守" in content or "倾向" in content:
        score += 1

    # 不泄露系统指令
    if "不暴露" not in content and "不泄露" not in content:
        # 这是合理的，因为 Skill 是指令不是敏感数据
        score += 1

    # 时区默认值
    if "Asia/Shanghai" in content or "默认" in content:
        score += 1

    result.add("安全与约束", score, 5, "; ".join(notes) if notes else "硬约束+保守策略+时区默认 完整")

    return result


def print_report(result):
    print("=" * 70)
    print("  AI Time Watch Skill — 质量评测报告")
    print("=" * 70)
    print()

    for name, dim in result.dimensions.items():
        bar_len = 20
        filled = int(dim["score"] / dim["max"] * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"  {name:<16s}  {bar}  {dim['score']}/{dim['max']}")
        if dim["note"]:
            print(f"  {'':16s}  → {dim['note']}")
        print()

    print("-" * 70)
    print(f"  总分: {result.total_score}/{result.max_score}  ({result.percentage()}%)")
    print(f"  评级: {result.grade()}")
    print("=" * 70)

    # 改进建议
    print()
    print("  改进建议:")
    print("  -" * 35)
    suggestions = []
    for name, dim in result.dimensions.items():
        if dim["score"] < dim["max"] * 0.7:
            suggestions.append(f"  [{name}] 得分 {dim['score']}/{dim['max']} — {dim['note']}")

    if suggestions:
        for s in suggestions:
            print(s)
    else:
        print("  无显著短板，所有维度均达到良好以上水平。")


if __name__ == "__main__":
    result = evaluate()
    print_report(result)