#!/usr/bin/env python3
"""Simple MCP server for mathematical calculations."""

import json
import sys
import math
from typing import Any


class CalculatorMCP:
    """MCP server providing calculation tools."""

    def __init__(self):
        self.tools = {
            "add": self._add,
            "subtract": self._subtract,
            "multiply": self._multiply,
            "divide": self._divide,
            "power": self._power,
            "sqrt": self._sqrt,
            "average": self._average,
        }

    def _add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def _subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        print(f"[SUBTRACT] Received: a={a}, b={b}", file=sys.stderr)
        return a - b

    def _multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    def _divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    def _power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        return base**exponent

    def _sqrt(self, number: float) -> float:
        """Calculate square root of number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(number)

    def _average(self, *numbers: float) -> float:
        """Calculate average of given numbers."""
        if not numbers:
            raise ValueError("At least one number required")
        return sum(numbers) / len(numbers)

    def list_tools(self) -> list[dict]:
        """Return available tools."""
        return [
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "subtract",
                "description": "Subtract two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Number to subtract"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "multiply",
                "description": "Multiply two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "divide",
                "description": "Divide a by b",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "Numerator"},
                        "b": {"type": "number", "description": "Denominator"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "power",
                "description": "Raise base to the power of exponent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base": {"type": "number", "description": "Base number"},
                        "exponent": {
                            "type": "number",
                            "description": "Exponent",
                        },
                    },
                    "required": ["base", "exponent"],
                },
            },
            {
                "name": "sqrt",
                "description": "Calculate square root",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "number": {
                            "type": "number",
                            "description": "Non-negative number",
                        }
                    },
                    "required": ["number"],
                },
            },
            {
                "name": "average",
                "description": "Calculate average of numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of numbers",
                        }
                    },
                    "required": ["numbers"],
                },
            },
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by name."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        func = self.tools[name]
        if name == "average":
            return func(*arguments.get("numbers", []))
        else:
            return func(**arguments)

    def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP request."""
        try:
            if request.get("method") == "tools/list":
                return {"tools": self.list_tools()}
            elif request.get("method") == "tools/call":
                result = self.call_tool(
                    request["params"]["name"], request["params"].get("arguments", {})
                )
                return {"result": result}
            else:
                return {"error": f"Unknown method: {request.get('method')}"}
        except Exception as e:
            return {"error": str(e)}


def main():
    """Run MCP server in stdio mode."""
    calculator = CalculatorMCP()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = calculator.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON"}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
