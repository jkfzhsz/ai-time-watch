"""
AI Time Watch Skill — 验证测试
测试 SKILL.md 的结构完整性和关键行为指令
"""
import os
import re
import sys

SKILL_PATH = r"d:\Trae\.trae\skills\ai-time-watch\SKILL.md"


def test_skill_file_exists():
    """SKILL.md 文件存在"""
    assert os.path.exists(SKILL_PATH), f"SKILL.md not found at {SKILL_PATH}"


def test_frontmatter_valid():
    """frontmatter 包含 name 和 description"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查 frontmatter 存在
    assert content.startswith("---\n"), "SKILL.md must start with frontmatter (---)"
    fm_end = content.find("---\n", 4)
    assert fm_end > 0, "Frontmatter not closed with ---"
    frontmatter = content[4:fm_end]

    assert 'name:' in frontmatter, "name field missing in frontmatter"
    assert 'description:' in frontmatter, "description field missing in frontmatter"

    # 提取 name
    name_match = re.search(r'name:\s*"([^"]+)"', frontmatter)
    assert name_match, "name must be quoted string"
    name = name_match.group(1)
    assert name == "ai-time-watch", f"Expected name='ai-time-watch', got '{name}'"

    # 提取 description
    desc_match = re.search(r'description:\s*"([^"]+)"', frontmatter)
    assert desc_match, "description must be quoted string"
    description = desc_match.group(1)
    assert len(description) > 10, "description too short"
    assert len(description) <= 200, f"description too long ({len(description)} chars)"

    print(f"  ✓ name: {name}")
    print(f"  ✓ description: {description[:80]}...")


def test_contains_tense_detection():
    """SKILL.md 包含时态检测指令"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 必须包含三时态关键词
    assert "过去" in content or "past" in content, "Missing 过去/past detection"
    assert "现在" in content or "present" in content, "Missing 现在/present detection"
    assert "将来" in content or "future" in content, "Missing 将来/future detection"


def test_contains_no_future_search_rule():
    """SKILL.md 包含'不搜索未来信息'的硬约束"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 必须有禁止搜索未来的指令
    has_rule = (
        "不搜索" in content or
        "不发起" in content or
        "禁止搜索" in content or
        "do not search" in content.lower() or
        "never search" in content.lower()
    )
    assert has_rule, "Missing hard constraint: do not search future information"


def test_contains_secondary_classification():
    """SKILL.md 包含将来事件的二次判定（预测型/定时型）"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "预测" in content or "predict" in content.lower(), "Missing 预测型 classification"
    assert "定时" in content or "schedule" in content.lower(), "Missing 定时型 classification"


def test_contains_schedule_integration():
    """SKILL.md 包含 Schedule 工具调用指令"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Schedule" in content, "Missing Schedule tool integration"


def test_contains_output_format():
    """SKILL.md 包含结构化输出格式说明"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "tense" in content, "Missing tense output field"
    assert "action" in content, "Missing action output field"


def test_contains_skip_rule():
    """SKILL.md 包含'无时间概念时跳过'的规则"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    has_skip = (
        "不触发" in content or
        "跳过" in content or
        "skip" in content.lower() or
        "无时间" in content
    )
    assert has_skip, "Missing skip rule for no-time input"


def test_skill_length_reasonable():
    """SKILL.md 长度合理（不过短也不过长）"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    assert len(lines) >= 30, f"SKILL.md too short ({len(lines)} lines), should be at least 30"
    assert len(lines) <= 500, f"SKILL.md too long ({len(lines)} lines), should be under 500"


# ============================================================
# AC 场景测试
# ============================================================

def test_ac1_past_detection():
    """AC-1: 输入含'昨天' → 输出 tense:past, action:reason"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # 必须包含"昨天"作为过去时态的示例，并输出 reason
    has_past_example = (
        ('"昨天"' in content or "'昨天'" in content or "昨天" in content) and
        ("past" in content.lower()) and
        ("reason" in content.lower())
    )
    assert has_past_example, "AC-1: Missing past tense detection with '昨天' → reason"


def test_ac2_present_detection():
    """AC-2: 输入含'现在'/'今天' → 输出 tense:present, action:reason"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    has_present = (
        (("现在" in content) or ("今天" in content)) and
        ("present" in content.lower()) and
        ("reason" in content.lower())
    )
    assert has_present, "AC-2: Missing present tense detection with '现在'/'今天' → reason"


def test_ac3_future_predict_no_search():
    """AC-3: 输入'明年市场规模' → future, predict, 不触发 WebSearch"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    has_future_predict = (
        ("明年" in content) and
        ("future" in content.lower()) and
        ("predict" in content.lower())
    )
    assert has_future_predict, "AC-3: Missing future-predict with '明年'"

    # 关键：必须包含禁止搜索未来的指令
    no_search = (
        "不搜索" in content or
        "不发起" in content or
        "禁止搜索" in content or
        "绝对不发起" in content
    )
    assert no_search, "AC-3: Missing hard constraint: no future search"


def test_ac4_future_schedule():
    """AC-4: 输入'每天下午5点' → future, schedule, should_schedule=true"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    has_schedule_example = (
        ("每天下午5点" in content or "每天" in content) and
        ("schedule" in content.lower()) and
        ("should_schedule" in content.lower())
    )
    assert has_schedule_example, "AC-4: Missing schedule example with '每天下午5点'"


def test_ac5_no_time_skip():
    """AC-5: 无时间概念 → Skill 不触发"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    has_skip = (
        "不触发" in content or
        "跳过" in content or
        "skip" in content.lower() or
        "静默" in content
    )
    assert has_skip, "AC-5: Missing skip/no-trigger rule for no-time input"


def test_ac6_schedule_cron_monday():
    """AC-6: 输入'下周一早上9点' → schedule, cron 对应周一 9:00"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # 必须包含 cron 表达式格式说明
    has_cron = (
        "cron_expression" in content.lower() or
        "cron" in content.lower()
    )
    assert has_cron, "AC-6: Missing cron expression in schedule output"
    # 必须包含时间映射参考（能将"周一9点"映射到 cron）
    has_time_mapping = (
        "周一" in content or
        "Monday" in content or
        "1-5" in content or
        "星期" in content or
        "0 9" in content
    )
    assert has_time_mapping, "AC-6: Missing weekday-to-cron mapping reference"


def test_ac7_multi_time():
    """AC-7: 多个时间概念 → 分别判定"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    has_multi = (
        "多个时间" in content or
        "多时间" in content or
        "multiple" in content.lower()
    )
    assert has_multi, "AC-7: Missing multi-time-concept handling rule"


# ============================================================
# Runner
# ============================================================
if __name__ == "__main__":
    tests = [
        test_skill_file_exists,
        test_frontmatter_valid,
        test_contains_tense_detection,
        test_contains_no_future_search_rule,
        test_contains_secondary_classification,
        test_contains_schedule_integration,
        test_contains_output_format,
        test_contains_skip_rule,
        test_skill_length_reasonable,
        # AC 场景测试
        test_ac1_past_detection,
        test_ac2_present_detection,
        test_ac3_future_predict_no_search,
        test_ac4_future_schedule,
        test_ac5_no_time_skip,
        test_ac6_schedule_cron_monday,
        test_ac7_multi_time,
    ]

    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✓ {test.__name__}")
        except AssertionError as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: ERROR - {e}")
            failed += 1

    print(f"\n{'='*50}")
    if failed == 0:
        print(f"ALL {len(tests)} TESTS PASSED ✓")
    else:
        print(f"{failed}/{len(tests)} TESTS FAILED ✗")
        sys.exit(1)