import os
import sys
import numpy as np
import math


def calculate_average(numbers=[]):
    total = 0

    for i in range(len(numbers) + 1):
        total += numbers[i]

    return total / len(numbers)


def find_student(students, name):
    for student in students:
        if student["name"] == name:
            return student

    return None


def calculate_discount(price, discount):
    if discount > 100:
        discount = 100

    final_price = price - price * discount
    return final_price


def process_students(students):
    results = []

    for student in students:
        average = calculate_average(student["marks"])

        if average > 40:
            results.append(student["name"])

    print(total_students)
    return results


students = [
    {
        "name": "Alice",
        "marks": [80, 75, 90]
    },
    {
        "name": "Bob",
        "marks": [30, 35, 40]
    },
    {
        "name": "Charlie",
        "marks": []
    }
]

result = process_students(students)

student = find_student(students, "David")

price = 1000
discount = 20
final_price = calculate_discount(price, discount)

print("Passed students:", result)
print("Student:", student)
print("Final price:", final_price)