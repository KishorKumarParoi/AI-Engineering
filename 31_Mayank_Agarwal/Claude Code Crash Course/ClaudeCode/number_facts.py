"""Module for analyzing and providing facts about numbers."""

import sys
import math


def is_prime(n):
    """
    Check if a number is prime.

    Args:
        n: Integer to check

    Returns:
        True if n is prime, False otherwise
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def is_perfect_square(n):
    """
    Check if a number is a perfect square.

    Args:
        n: Integer to check

    Returns:
        True if n is a perfect square, False otherwise
    """
    if n < 0:
        return False
    sqrt = int(math.sqrt(n))
    return sqrt * sqrt == n


def is_fibonacci(n):
    """
    Check if a number is a Fibonacci number.

    Args:
        n: Integer to check

    Returns:
        True if n is a Fibonacci number, False otherwise
    """
    if n < 0:
        return False
    return is_perfect_square(5 * n * n + 4) or is_perfect_square(5 * n * n - 4)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Please provide a number as an argument.")
        print("Usage: python number_facts.py <number>")
        sys.exit(1)

    try:
        num = int(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid integer.")
        sys.exit(1)

    print(f"\n=== Number Facts for {num} ===")
    print(f"Prime:          {is_prime(num)}")
    print(f"Perfect Square: {is_perfect_square(num)}")
    print(f"Fibonacci:      {is_fibonacci(num)}\n")
