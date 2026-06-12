import ast
import inspect
from typing import Dict, Any
from unittest import result
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from langsmith import traceable

@traceable(
    name="format_ai_message",
    run_type="llm",
    tags=["utility"]
)
def format_ai_message(response):
    raw_response = response
    if isinstance(response, (tuple, list)):
        response = response[0] if response else None

    if response and getattr(response, "tool_calls", None):
        tool_calls = []
        for i, tc in enumerate(response.tool_calls):
            tool_args = getattr(tc, "args", None)
            if tool_args is None:
                tool_args = getattr(tc, "arguments", {})

            tool_name = getattr(tc, "name", None)
            if tool_name is None:
                tool_name = getattr(tc, "tool_name", "")

            tool_calls.append({
               "id": f"call_{i}",
               "name": tool_name,
               "args": tool_args
            })

        ai_message = AIMessage(content=getattr(response, "answer", ""), tool_calls=tool_calls)
    else:
        answer_text = getattr(response, "answer", None)
        if answer_text is None and isinstance(raw_response, (tuple, list)) and raw_response:
            answer_text = getattr(raw_response[0], "answer", "")
        ai_message = AIMessage(content=answer_text or "")
    
    return ai_message

@traceable(
    name="format_human_message",
    run_type="llm",
    tags=["utility"]
)
def parse_function_definition(function_def: str) -> Dict[str, Any]:
    """
    Parses a function definition string to extract metadata including type hints.
    """
    result = {
        "name": "",
        "description": "",
        "parameters": {"type": "object", "properties": {}},
        "required": [],
        "returns": {"type": "string", "description": ""}
    }

    # parse the function using ast
    tree = ast.parse(function_def.strip())
    if not tree.body or not isinstance(tree.body[0], ast.FunctionDef):
        return result 
    
    func = tree.body[0]
    result["name"] = func.name

    docstring = ast.get_docstring(func) or ""
    if docstring:
        desc_end = docstring.find("\n\n") if '\n\n' in docstring else docstring.find('\nArgs:')
        desc_end = desc_end if desc_end != -1 else docstring.find('\nParameters:')
        result['description'] = docstring[:desc_end].strip() if desc_end != -1 else docstring.strip()

        params_descs = parse_docstring_params(docstring)

        if 'Returns' in docstring:
            result["returns"]["description"] = docstring.split("Returns:")[1].strip().split("\n")[0]
        
    args = func.args
    defaults = args.defaults
    num_args = len(args.args)
    num_defaults = len(defaults)

    for i, arg in enumerate(args.args):
        if arg.arg == 'self':
            continue
        param_info = {
            "type": get_type_from_annotation(arg.annotation) if arg.annotation else "string",
            "description": params_descs.get(arg.arg, "")
        }

        default_idx = i - (num_args - num_defaults)

        if default_idx >= 0:
            param_info["default"] = ast.literal_eval(ast.unparse(defaults[default_idx]))
        else:
            result["required"].append(arg.arg)
        
        result["parameters"]["properties"][arg.arg] = param_info

    if func.returns:
        result["returns"]["type"] = get_type_from_annotation(func.returns)

    return result

@traceable(
    name="get_type_from_annotation",
    run_type="llm",
    tags=["utility"]
)
def get_type_from_annotation(annotation) -> str:
    """Converts a type annotation AST node to a string representation."""

    if not annotation:
        return "string"
    type_map = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "dict": "object",
        "List": "array",
        "Dict": "object",
        "Any": "any"
    }

    if isinstance(annotation, ast.Name):
        return type_map.get(annotation.id, annotation.id)
    elif isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
        base_type = annotation.value.id
        if base_type in ["List", "Dict"]:
            return type_map.get(base_type, base_type)
    return "string"

@traceable(
    name="parse_docstring_params",
    run_type="llm",
    tags=["utility"]
)
def parse_docstring_params(docstring: str) -> Dict[str, str]:
    """Extract parameter description from docstring (handles both Args: and parameters: formats)"""
    params = {}
    lines = docstring.split("\n")
    in_params = False
    current_param = None

    for line in lines:
        stripped = line.strip()
        if stripped in ["Args:", "Parameters:", "Arguments:", "Params:"]:
            in_params = True
            current_param = None
        elif stripped.startswith("Returns:") or stripped.startswith("Raises:"):
            in_params = False
        elif in_params:
            if ':' in stripped and (stripped[0].isalpha() or stripped.startswith('-', '*')):
                param_name = stripped.lstrip('- *').split(':')[0].strip()
                params_desc = ':'.join(stripped.lstrip('- *').split(':')[1:]).strip()
                params[param_name] = params_desc
                current_param = param_name
            elif current_param and stripped:
                params[current_param] += ' ' + stripped
    return params

@traceable(
    name="get_tool_descriptions",
    run_type="llm",
    tags=["utility"]
)
def get_tool_descriptions(function_list):
    """Extract tool descriptions from the function list."""
    descriptions = []

    for function in function_list:
        function_string = inspect.getsource(function)
        result = parse_function_definition(function_string)

        if result:
            descriptions.append(result)

    return descriptions if descriptions else "Could not extract tool descriptions."