"""
Candidate implementation file.

See interview_question.md for the full spec. Implement resolve_tool_call
below. Do not change its signature.
"""

import json
import inspect


def resolve_tool_call(responses: list, registry: dict) -> dict:
    """
    Try each string in `responses`, in order, until one resolves to a
    valid direct answer or a valid + successfully-executed tool call.

    See interview_question.md for the full validity rules and return
    shape.
    """
    retries:int=0

    returned_responses:dict[str, str]={}

    for response in responses:
        retries+=1
        try:
            parsed_response = json.loads(response)
        except json.JSONDecodeError:
            continue  # skip invalid JSON

        if not isinstance(parsed_response, dict):
            continue  # skip if not a dict

        tool_name = parsed_response.get("tool")
        args = parsed_response.get("args")
        answer=parsed_response.get("answer")

        if tool_name is None and not answer:
            continue  # skip if both tool and answer are missing

        if tool_name is None and (answer is not None):
            returned_responses = {"status":"ok", "tool": None, "result":parsed_response.get("answer"), "attempts": retries}
            return {"status":"ok", "tool": None, "result":parsed_response.get("answer"), "attempts": retries}  #if result and tool is none, return result
            #continue

        if tool_name not in registry:
            continue  

        tool_func = registry[tool_name]
        sig = inspect.signature(tool_func)

        try:
            sig.bind(**args)  # check if args match the function signature
        except TypeError:
            continue  # skip if args do not match

        try:
            result = tool_func(**args)
            return {"status": "ok", "tool": tool_name, "result": result, "attempts": retries}
        except Exception as e:
            continue

    return {"status": "error", "reason":"exhausted retries", "attempts": retries}    

# --- Sample tools/registry for manual testing during the interview ---------

def calculate_tip(bill_amount: float, tip_percent: float) -> float:
    return round(bill_amount * (tip_percent / 100), 2)

def add(a: int, b: int) -> int:
    return a + b


def get_order_status(order_id: str) -> str:
    fake_db = {"A123": "shipped", "B456": "processing"}
    return fake_db.get(order_id, "order not found")


SAMPLE_REGISTRY = {
    "calculate_tip": calculate_tip,
    "get_order_status": get_order_status,
}

if __name__ == "__main__":
    # Quick manual sanity check
    responses = [
        '{"tool": "calculate_tip", "args": {"bill_amount": 84.50}}',  # missing arg -> fail
        '{"tool": "calculate_tip", "args": {"bill_amount": 84.50, "tip_percent": 18}}',
    ]
    print(resolve_tool_call(responses, SAMPLE_REGISTRY))
