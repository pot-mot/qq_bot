import random
import unittest
from typing import List, Union, Optional
from dataclasses import dataclass


@dataclass
class DiceRollInfo:
    """
    骰子投掷信息的数据类
    """
    count: int
    sides: int
    rolls: List[int]
    result: int

    def __str__(self) -> str:
        if self.count > 1:
            return f"{self.count}D{self.sides}={'+'.join(map(str, self.rolls))}={self.result}"
        else:
            return f"D{self.sides}={self.result}"


all_precedence = "+-*/%^d()"
left_precedence = "+-*/%^("
right_precedence = "+-*/%^)"

precedence: dict[str, int] = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3, 'd': 4, 'P': 5, 'N': 5}
right_associative: set[str] = {'^', 'd', 'P', 'N'}


def tokenize(expression: str) -> List[Union[int, float, str]]:
    """
    将表达式字符串分解为标记列表
    """
    expression = expression.replace(' ', '')
    tokens: List[Union[int, float, str]] = []
    i: int = 0
    while i < len(expression):
        if expression[i].isdigit() or expression[i] == '.':
            # 处理数字（包括小数）
            start: int = i
            while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
                i += 1
            tokens.append(float(expression[start:i]) if '.' in expression[start:i] else int(expression[start:i]))
        elif expression[i] in all_precedence:
            # 处理一元正号的情况：如果+号在开头或前面是另一个运算符或左括号
            if (
                    expression[i] == '+' and (
                    i == 0 or (i > 0 and (isinstance(expression[i - 1], str) and expression[i - 1] in left_precedence)))
            ):
                tokens.append('P')
                i += 1
            # 处理一元负号的情况：如果-号在开头或前面是另一个运算符或左括号
            elif (
                    expression[i] == '-' and (
                    i == 0 or (i > 0 and (isinstance(expression[i - 1], str) and expression[i - 1] in left_precedence)))
            ):
                tokens.append('N')
                i += 1
            # 特如果当前是'd'且下一个有效字符是运算符或表达式结束
            elif (
                    expression[i] == 'd' and
                    (i + 1 >= len(expression) or expression[i + 1] in right_precedence)
            ):
                tokens.append('d')
                tokens.append(100)
                i += 1
            else:
                tokens.append(expression[i])
                i += 1
        else:
            raise ValueError(f"非法字符: {expression[i]}")
    return tokens


def infix_to_postfix(tokens: List[Union[int, float, str]]) -> List[Union[int, float, str]]:
    """
    使用调度场算法将中缀表达式转换为后缀表达式（逆波兰表示法）
    """
    output: List[Union[int, float, str]] = []
    operator_stack: List[str] = []

    for i, token in enumerate(tokens):
        if isinstance(token, (int, float)):
            # 如果是数字，直接加入输出队列
            output.append(token)
        elif token in precedence:
            # 处理一元d运算符的情况
            if token == 'd' and (
                    i == 0 or (i > 0 and (isinstance(tokens[i - 1], str) and tokens[i - 1] in left_precedence))):
                # 如果d前面是运算符或表达式开始，则在前面加一个1作为默认骰子数量
                output.append(1)

            # 判断运算符优先级
            while (operator_stack and
                   operator_stack[-1] != '(' and
                   operator_stack[-1] in precedence and
                   (precedence[operator_stack[-1]] > precedence[token] or
                    (precedence[operator_stack[-1]] == precedence[token] and
                     token not in right_associative))):
                output.append(operator_stack.pop())
            operator_stack.append(token)
        elif token == '(':
            # 左括号直接入栈
            operator_stack.append(token)
        elif token == ')':
            # 右括号：弹出运算符直到遇到左括号
            while operator_stack and operator_stack[-1] != '(':
                output.append(operator_stack.pop())
            if not operator_stack:
                raise ValueError("括号不匹配")
            operator_stack.pop()  # 弹出左括号

    # 弹出剩余运算符
    while operator_stack:
        if operator_stack[-1] in '()':
            raise ValueError("括号不匹配")
        output.append(operator_stack.pop())

    return output


def evaluate_postfix(postfix_tokens: List[Union[int, float, str]],
                     dice_details: Optional[List[DiceRollInfo]] = None) -> Union[int, float]:
    """
    计算后缀表达式的值
    :param postfix_tokens: 后缀表达式标记列表
    :param dice_details: 可选参数，用于记录骰子投掷的详细信息
    """
    stack: List[Union[int, float]] = []

    for token in postfix_tokens:
        if isinstance(token, (int, float)):
            stack.append(token)
        elif token == 'P':
            if len(stack) < 1:
                raise ValueError("表达式格式错误")
            stack.append(stack.pop())
        elif token == 'N':
            if len(stack) < 1:
                raise ValueError("表达式格式错误")
            stack.append(-stack.pop())
        elif token == 'd':
            if len(stack) < 2:
                raise ValueError("表达式格式错误")

            sides: Union[int, float] = stack.pop()
            count: Union[int, float] = stack.pop()

            # 骰子运算需要整数参数
            if count <= 0 or sides <= 0:
                raise ValueError("骰子参数必须是正数")
            if isinstance(sides, float):
                sides = int(sides)
            if isinstance(count, float):
                count = int(count)

            # 执行骰子投掷
            rolls = [random.randint(1, sides) for _ in range(count)]
            roll_result = sum(rolls)
            stack.append(roll_result)

            # 记录骰子投掷详情（如果提供了记录参数）
            if dice_details is not None:
                dice_details.append(DiceRollInfo(
                    count=count,
                    sides=sides,
                    rolls=rolls,
                    result=roll_result
                ))
        elif token in precedence:
            if len(stack) < 2:
                raise ValueError("表达式格式错误")

            b: Union[int, float] = stack.pop()
            a: Union[int, float] = stack.pop()

            if token == '+':
                stack.append(a + b)
            elif token == '-':
                stack.append(a - b)
            elif token == '*':
                stack.append(a * b)
            elif token == '/':
                if b == 0:
                    raise ValueError("除零错误")
                stack.append(a / b)
            elif token == '%':
                if b == 0:
                    raise ValueError("除零错误")
                stack.append(a % b)
            elif token == '^':
                stack.append(a ** b)

    if len(stack) != 1:
        raise ValueError("表达式格式错误")

    return stack[0]


def calculate(expression: str,
              dice_details: Optional[List[DiceRollInfo]] = None) -> Union[int, float]:
    """
    计算中缀表达式的值
    :param expression: 中缀表达式字符串
    :param dice_details: 可选参数，用于记录骰子投掷的详细信息
    :return: 计算结果
    """
    # 1. 分词
    tokens: List[Union[int, float, str]] = tokenize(expression)
    # 2. 转换为后缀表达式
    postfix: List[Union[int, float, str]] = infix_to_postfix(tokens)
    # 3. 计算后缀表达式
    return evaluate_postfix(postfix, dice_details)


class TestDiceInfixCalculator(unittest.TestCase):
    def test_basic_arithmetic_1(self):
        """测试基本算术运算: 3 + 4 - 2"""
        result = calculate("3 + 4 - 2")
        self.assertEqual(5, result)

    def test_exponentiation_1(self):
        """测试指数运算: 2 ^ 3"""
        result = calculate("2 ^ 3")
        self.assertEqual(8, result)

    def test_right_associative_exponentiation(self):
        """测试右结合指数运算: 2 ^ 3 ^ 2"""
        result = calculate("2 ^ 3 ^ 2")
        self.assertEqual(512, result)  # 2^(3^2) = 2^9 = 512

    def test_negative_number_addition(self):
        """测试负数加法: -3 + 4"""
        result = calculate("-3 + 4")
        self.assertEqual(1, result)
        result = calculate("4 + -3")
        self.assertEqual(1, result)

    def test_parenthesized_negative_exponentiation(self):
        """测试括号中的负数指数运算: (-2) ^ 2"""
        result = calculate("(-2) ^ 2")
        self.assertEqual(4, result)
        result = calculate("-2 ^ 2")
        self.assertEqual(4, result)
        result = calculate("- (2 ^ 2)")
        self.assertEqual(-4, result)

    def test_negative_multi(self):
        result = calculate("2 * -3")
        self.assertEqual(-6, result)

    def test_many_negative_or_positive(self):
        result = calculate("--2")
        self.assertEqual(2, result)

        result = calculate("-+2 + -+-+3")
        self.assertEqual(1, result)

    def test_negative_bucket(self):
        result = calculate("- (2 + 2)")
        self.assertEqual(-4, result)

    def test_mod(self):
        result = calculate("5 % 2")
        self.assertEqual(1, result)

    def test_float_multiplication(self):
        """测试浮点数乘法: 2.0 * 2"""
        result = calculate("2.0 * 2")
        self.assertAlmostEqual(4.0, result)

    def test_float_division_1(self):
        """测试浮点数除法: 2.0 / 2"""
        result = calculate("2.0 / 2")
        self.assertAlmostEqual(1.0, result)

    def test_division_result_fraction(self):
        """测试除法结果为分数: 1 / 3"""
        result = calculate("1 / 3")
        self.assertAlmostEqual(1 / 3, result)

    def test_float_arithmetic_chain(self):
        """测试浮点数算术链: 1.0 / 3.0 * 3"""
        result = calculate("1.0 / 3.0 * 3")
        self.assertAlmostEqual(1.0, result)

    def test_fractional_exponentiation(self):
        """测试小数指数运算: 2 ^ 0.2"""
        result = calculate("2 ^ 0.2")
        self.assertAlmostEqual(2 ** 0.2, result)

    def test_exponentiation_with_parentheses(self):
        """测试带括号的指数运算: 2 ^ (0.5 * 2)"""
        result = calculate("2 ^ (0.5 * 2)")
        self.assertEqual(2.0, result)

    def test_single_d20_dice(self):
        """测试单个20面骰子: d20"""
        dice_info: List[DiceRollInfo] = []
        result = calculate("d20", dice_info)
        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 20)
        self.assertEqual(len(dice_info), 1)
        self.assertEqual(dice_info[0].count, 1)
        self.assertEqual(dice_info[0].sides, 20)
        self.assertEqual(len(dice_info[0].rolls), 1)
        self.assertEqual(dice_info[0].result, result)

    def test_two_d6_dice(self):
        """测试2个6面骰子: 2d6"""
        dice_info: List[DiceRollInfo] = []
        result = calculate("2d6", dice_info)
        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 2)  # 最小值 1+1=2
        self.assertLessEqual(result, 12)  # 最大值 6+6=12
        self.assertEqual(len(dice_info), 1)
        self.assertEqual(dice_info[0].count, 2)
        self.assertEqual(dice_info[0].sides, 6)
        self.assertEqual(len(dice_info[0].rolls), 2)
        self.assertEqual(sum(dice_info[0].rolls), result)

    def test_dice_multiplication(self):
        """测试骰子乘法: 2 * d10"""
        dice_info: List[DiceRollInfo] = []
        result = calculate("2 * d10", dice_info)
        self.assertIsInstance(result, (int, float))
        # d10的结果在1-10之间，乘以2后应在2-20之间
        self.assertGreaterEqual(result, 2)
        self.assertLessEqual(result, 20)
        self.assertEqual(len(dice_info), 1)
        self.assertEqual(dice_info[0].count, 1)
        self.assertEqual(dice_info[0].sides, 10)

    def test_nested_dice_expression(self):
        """测试嵌套骰子表达式: (2d4)d6"""
        dice_info: List[DiceRollInfo] = []
        result = calculate("(2d4)d6", dice_info)
        self.assertIsInstance(result, (int, float))
        # 2d4的结果在2-8之间，表示骰子数量
        # 然后投掷相应数量的d6骰子，每个骰子结果在1-6之间
        # 最小值: 2个骰子，每个1点 = 2
        # 最大值: 8个骰子，每个6点 = 48
        self.assertGreaterEqual(result, 2)
        self.assertLessEqual(result, 48)
        self.assertEqual(len(dice_info), 2)  # 应该有两个骰子信息记录

    def test_dice_addition(self):
        """测试骰子加法: 3d6 + 2d8"""
        dice_info: List[DiceRollInfo] = []
        result = calculate("3d6 + 2d8", dice_info)
        self.assertIsInstance(result, (int, float))
        # 3d6范围: 3-18, 2d8范围: 2-16
        # 总和范围: 5-34
        self.assertGreaterEqual(result, 5)
        self.assertLessEqual(result, 34)
        self.assertEqual(len(dice_info), 2)  # 应该有两个骰子信息记录

    def test_calculated_dice_sides(self):
        """测试计算得出的骰子面数: 3d( 2 + 4 )"""
        dice_info: List[DiceRollInfo] = []
        result = calculate("3d( 2 + 4 )", dice_info)
        self.assertIsInstance(result, (int, float))
        # 等同于3d6，范围应在3-18之间
        self.assertGreaterEqual(result, 3)
        self.assertLessEqual(result, 18)
        self.assertEqual(len(dice_info), 1)
        self.assertEqual(dice_info[0].count, 3)
        self.assertEqual(dice_info[0].sides, 6)

    def test_d_followed_by_operator(self):
        """测试d后面跟着运算符的情况: 2d+3"""
        dice_info: List[DiceRollInfo] = []
        result = calculate("2d+3", dice_info)
        self.assertIsInstance(result, (int, float))
        # 2d100范围: 2-200，加3后范围: 5-203
        self.assertGreaterEqual(result, 5)
        self.assertLessEqual(result, 203)
        self.assertEqual(len(dice_info), 1)
        self.assertEqual(dice_info[0].count, 2)
        self.assertEqual(dice_info[0].sides, 100)

    def test_complex_dice_expression(self):
        """测试复杂骰子表达式: 2d2d2"""
        # 这个表达式实际上是有效的: (2d2)d2
        # 第一步2d2结果为2-4，第二步用这个结果作为骰子数量投掷d2
        dice_info: List[DiceRollInfo] = []
        result = calculate("2d2d2", dice_info)
        self.assertIsInstance(result, (int, float))
        # 2d2范围: 2-4
        # 然后用这个结果作为骰子数量投掷d2 (每个骰子1-2点)
        # 最小值: 2个骰子，每个1点 = 2
        # 最大值: 4个骰子，每个2点 = 8
        self.assertGreaterEqual(result, 2)
        self.assertLessEqual(result, 8)
        self.assertGreaterEqual(len(dice_info), 1)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
