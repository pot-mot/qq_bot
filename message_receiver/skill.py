import re
import unittest
from typing import Optional, List
from unittest.mock import patch

from dice import calculate, DiceRollInfo
from user import CharacterInfo


def pass_skill_value_expression(
        expression: str,
        dice_details: Optional[List[DiceRollInfo]] = None,
        default_sides: int = 100
) -> dict[str, int]:
    """
    解析技能表达式，将形如"强化50力量50buff54"的字符串解析为字典

    Args:
        expression: 技能表达式字符串
        dice_details: 可选参数，用于记录骰子投掷的详细信息
        default_sides: 默认骰子面数

    Returns:
        dict[str, int]: 解析后的键值对字典
    """
    expression = expression.replace(" ", "")

    # 分割字符串
    parts = re.findall(r'[^0-9d+\-*/^%()]+|[0-9d+\-*/^%()]+', expression)

    # 移除空字符串
    parts = [part for part in parts if len(part) > 0]

    result = {}
    i = 0

    # 检查是否以骰子表达式开头
    if parts and re.match(r'^[0-9d+\-*/^%()]+$', parts[0]):
        i = 1  # 跳过第一个元素

    # 交替处理键和值
    while i < len(parts):
        # 键（文本部分）
        key = parts[i]
        i += 1

        # 值（数字部分）
        if i < len(parts):
            value_str = parts[i]
            # 尝试转换为整数
            try:
                value = calculate(value_str, dice_details, default_sides)
                if isinstance(value, float):
                    value = int(value)
            except Exception:
                value = 0
            result[key] = value
            i += 1
        else:
            # 如果没有对应的值，默认为0
            result[key] = 0

    return result



class SkillRollResult:
    skill_name: str
    skill_value: int
    roll_result: int
    dice_details: List[DiceRollInfo]
    success_type: str


def calculate_skill_roll_expression(
        expression: str,
        character_info: CharacterInfo,
        default_sides: int = 100
) -> SkillRollResult:
    """
    计算技能投掷表达式，将形如"强化", "强化50"的字符串解析为结果

    Args:
        expression: 技能表达式字符串
        character_info: 角色信息
        default_sides: 默认骰子面数

    Returns:
        SkillRollResult: 技能检定结果
    """
    # 解析表达式
    parts = re.findall(r'[^0-9d+\-*/^%()]+|[0-9d+\-*/^%()]+', expression)
    parts = [part for part in parts if len(part) > 0]

    # 默认技能名和技能值
    skill_name = ""
    skill_value = 0

    # 提取技能名和目标值
    if parts:
        if len(parts) >= 1:
            skill_name = parts[0]
            # 检查是否有指定的目标值
            if len(parts) > 1 and re.match(r'^[0-9d+\-*/^%()]+$', parts[1]):
                try:
                    skill_value = calculate(parts[1], default_sides=default_sides)
                    if isinstance(skill_value, float):
                        skill_value = int(skill_value)
                except Exception:
                    # 如果计算失败，从角色信息中获取技能值
                    skill_value = character_info.skills.get(skill_name, 0)
            else:
                # 从角色信息中获取技能值
                skill_value = character_info.skills.get(skill_name, 0)
        else:
            # 如果以数值开头，可能是直接指定目标值的情况
            try:
                skill_value = calculate(parts[0], default_sides=default_sides)
                if isinstance(skill_value, float):
                    skill_value = int(skill_value)
            except Exception:
                skill_value = 0

    # 执行骰子投掷
    dice_details = []
    roll_result = calculate(f"1d{100 if skill_value < 100 else skill_value}", dice_details, default_sides=100)
    if isinstance(roll_result, float):
        roll_result = int(roll_result)

    # 创建结果对象
    result = SkillRollResult()
    result.skill_name = skill_name
    result.skill_value = skill_value
    result.roll_result = roll_result
    result.dice_details = dice_details
    result.success_type = determine_success_type(roll_result, skill_value)

    return result


def determine_success_type(roll_result: int, target_value: int, super_range: int = 5) -> str:
    """
    根据投掷结果和目标值确定成功类型

    Args:
        roll_result: 骰子投掷结果 (1-100)
        target_value: 技能目标值

    Returns:
        str: 成功类型
    """
    # 大成功判定
    if (target_value >= super_range * 5 and roll_result <= super_range) or (roll_result <= roll_result // 5):
        return "大成功"

    # 大失败判定
    if target_value <= 100 and roll_result >= (100 - super_range):
        return "大失败"

    # 根据目标值确定成功等级
    hard_success = target_value // 2  # 困难成功线
    extreme_success = target_value // 4  # 极难成功线

    if roll_result <= extreme_success:
        return "极难成功"
    elif roll_result <= hard_success:
        return "困难成功"
    elif roll_result <= target_value:
        return "成功"
    else:
        return "失败"



class TestPassSkillExpressionWithMock(unittest.TestCase):
    @patch('skill.calculate')
    def test_with_mocked_dice_calculate(self, mock_calculate):
        """使用mock测试包含骰子表达式的解析"""
        # 设置mock的返回值
        mock_calculate.side_effect = lambda x, default_sides: {
            '50': 50,
            '20': 20,
            '1d100': 42,
            '1d6': 3
        }.get(x, 0)

        # 测试以骰子表达式开头
        result = pass_skill_value_expression("1d100强化50")
        expected = {"强化": 50}
        self.assertEqual(expected, result)

        # 测试包含骰子表达式的值
        result = pass_skill_value_expression("强化1d6力量50")
        expected = {"强化": 3, "力量": 50}
        self.assertEqual(expected, result)

        result = pass_skill_value_expression("强化1d6力量50Skill")
        expected = {"强化": 3, "力量": 50, "Skill": 0}
        self.assertEqual(expected, result)

        result = pass_skill_value_expression("强化1d6力量50Skill20")
        expected = {"强化": 3, "力量": 50, "Skill": 20}
        self.assertEqual(expected, result)

        result = pass_skill_value_expression("强化1d6力量50Skill20Default")
        expected = {"强化": 3, "力量": 50, "Skill": 20, "Default": 0}
        self.assertEqual(expected, result)

if __name__ == '__main__':
    # 可以单独运行这个测试类
    unittest.main()