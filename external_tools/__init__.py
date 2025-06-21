import re

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b

def verify(submission, solution):
    pattern = r'####\s*(-?\d+(?:\.\d+)?)'
    solution =float(re.findall(pattern, solution)[0])
    return submission == solution