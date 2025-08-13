# from typing import List, Union
#
#
# class InfixCalculator:
#     def __init__(self) -> None:
#         # 定义运算符优先级，^ 的优先级高于 * 和 /
#         self.precedence: dict[str, int] = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
#         # 定义右结合运算符，^ 是右结合的
#         self.right_associative: set[str] = {'^'}
#
#     @staticmethod
#     def tokenize(expression: str) -> List[Union[int, float, str]]:
#         """
#         将表达式字符串分解为标记列表
#         """
#         tokens: List[Union[int, float, str]] = []
#         i: int = 0
#         while i < len(expression):
#             if expression[i].isspace():
#                 i += 1
#                 continue
#             elif expression[i].isdigit() or expression[i] == '.':
#                 # 处理数字（包括小数）
#                 start: int = i
#                 while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
#                     i += 1
#                 tokens.append(float(expression[start:i]) if '.' in expression[start:i] else int(expression[start:i]))
#             elif expression[i] in '+-*/()^':
#                 tokens.append(expression[i])
#                 i += 1
#             else:
#                 raise ValueError(f"非法字符: {expression[i]}")
#         return tokens
#
#     def infix_to_postfix(self, tokens: List[Union[int, float, str]]) -> List[Union[int, float, str]]:
#         """
#         使用调度场算法将中缀表达式转换为后缀表达式（逆波兰表示法）
#         """
#         output: List[Union[int, float, str]] = []
#         operator_stack: List[str] = []
#
#         for i, token in enumerate(tokens):
#             if isinstance(token, (int, float)):
#                 # 如果是数字，直接加入输出队列
#                 output.append(token)
#             elif token in self.precedence:
#                 # 如果是运算符
#                 # 处理一元负号的情况：如果-号在开头或前面是另一个运算符或左括号
#                 if token == '-' and (i == 0 or tokens[i - 1] in '+-*/(^'):
#                     # 这里简化处理，将一元负号转换为二元减法，前面加一个0
#                     output.append(0)
#
#                 while (operator_stack and
#                        operator_stack[-1] != '(' and
#                        operator_stack[-1] in self.precedence and
#                        (self.precedence[operator_stack[-1]] > self.precedence[token] or
#                         (self.precedence[operator_stack[-1]] == self.precedence[token] and
#                          token not in self.right_associative))):
#                     output.append(operator_stack.pop())
#                 operator_stack.append(token)
#             elif token == '(':
#                 # 左括号直接入栈
#                 operator_stack.append(token)
#             elif token == ')':
#                 # 右括号：弹出运算符直到遇到左括号
#                 while operator_stack and operator_stack[-1] != '(':
#                     output.append(operator_stack.pop())
#                 if not operator_stack:
#                     raise ValueError("括号不匹配")
#                 operator_stack.pop()  # 弹出左括号
#
#         # 弹出剩余运算符
#         while operator_stack:
#             if operator_stack[-1] in '()':
#                 raise ValueError("括号不匹配")
#             output.append(operator_stack.pop())
#
#         return output
#
#     def evaluate_postfix(self, postfix_tokens: List[Union[int, float, str]]) -> Union[int, float]:
#         """
#         计算后缀表达式的值
#         """
#         stack: List[Union[int, float]] = []
#
#         for token in postfix_tokens:
#             if isinstance(token, (int, float)):
#                 stack.append(token)
#             elif token in self.precedence:
#                 if len(stack) < 2:
#                     raise ValueError("表达式格式错误")
#
#                 b: Union[int, float] = stack.pop()
#                 a: Union[int, float] = stack.pop()
#
#                 if token == '+':
#                     stack.append(a + b)
#                 elif token == '-':
#                     stack.append(a - b)
#                 elif token == '*':
#                     stack.append(a * b)
#                 elif token == '/':
#                     if b == 0:
#                         raise ValueError("除零错误")
#                     stack.append(a / b)
#                 elif token == '^':
#                     stack.append(a ** b)
#
#         if len(stack) != 1:
#             raise ValueError("表达式格式错误")
#
#         return stack[0]
#
#     def calculate(self, expression: str) -> Union[int, float]:
#         """
#         计算中缀表达式的值
#         """
#         # 1. 分词
#         tokens: List[Union[int, float, str]] = self.tokenize(expression)
#         # 2. 转换为后缀表达式
#         postfix: List[Union[int, float, str]] = self.infix_to_postfix(tokens)
#         # 3. 计算后缀表达式
#         return self.evaluate_postfix(postfix)
#
#
# # 使用示例
# if __name__ == "__main__":
#     calculator = InfixCalculator()
#
#     # 测试用例
#     test_expressions: List[str] = [
#         "3 + 4 * -2",
#         "2 ^ 3",
#         "2 ^ 3 ^ 2",
#         "-3 + 4",
#         "(-2) ^ 2",
#         "2 * -3 + 1",
#         "2.0 * 2",
#         "2.0 / 2",
#         "1 / 3",
#         "1.0 / 3.0 * 3",
#         "2 ^ 0.2",
#         "2 ^ (0.5 * 2)"
#     ]
#
#     for expr in test_expressions:
#         try:
#             result: Union[int, float] = calculator.calculate(expr)
#             print(f"{expr} = {result}")
#         except Exception as e:
#             print(f"{expr} -> 错误: {e}")
