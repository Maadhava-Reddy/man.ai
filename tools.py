import datetime
import os


def get_current_time() -> str:
    return datetime.datetime.now().isoformat()


def calculate(expression: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Error: expression contains disallowed characters."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"


def read_text_file(path: str) -> str:
    if not os.path.exists(path):
        return f"Error: file not found at {path}"
    with open(path, "r") as f:
        return f.read()[:2000]


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time. Use when the user asks what time/date it is.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a basic arithmetic expression, e.g. '12 * (3 + 4)'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A math expression using only numbers and + - * / ( )",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_text_file",
            "description": "Read the contents of a local text file given its path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the text file"
                    }
                },
                "required": ["path"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "read_text_file": read_text_file,
}