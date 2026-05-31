import sys
import os

from backend.converter.python_to_cpp import PythonToCppConverter

def test_code(code_str):
    converter = PythonToCppConverter()
    print("----- Python Code -----")
    print(code_str)
    print("-----------------------")
    res = converter.convert(code_str)
    print("Warnings:", res.get('warnings', []))
    print("C++ Code:")
    print(res.get('code', ''))
    print("=======================\n")

test_cases = [
"""
def add(a, b):
    return a + b

print(add(5, 10))
""",
"""
x = 10
if x > 5:
    print("x is big")
elif x == 5:
    print("x is 5")
else:
    print("x is small")
""",
"""
for i in range(10):
    print(i)
""",
"""
def greet(name):
    print("Hello", name)

greet("World")
""",
"""
x = [1, 2, 3]
for i in x:
    print(i)
"""
]

for i, tc in enumerate(test_cases):
    print(f"Test case {i+1}")
    test_code(tc)
