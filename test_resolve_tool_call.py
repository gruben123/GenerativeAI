"""
Grading suite for the mock interview question.

By default this imports the candidate's implementation from
candidate_stub.py. To grade the answer key instead, set:

    IMPL_MODULE=reference_solution pytest test_resolve_tool_call.py -v
"""

import os
import importlib
import pytest

IMPL_MODULE = os.environ.get("IMPL_MODULE", "candidate_stub")
impl = importlib.import_module(IMPL_MODULE)
resolve_tool_call = impl.resolve_tool_call


def add(a: int, b: int) -> int:
    return a + b


def boom(a: int) -> int:
    raise ValueError("simulated tool failure")


REGISTRY = {"add": add, "boom": boom}


def test_direct_answer_no_tool_needed():
    responses = ['{"tool": null, "answer": "Paris is the capital of France."}']
    result = resolve_tool_call(responses, REGISTRY)
    assert result == {
        "status": "ok",
        "tool": None,
        "result": "Paris is the capital of France.",
        "attempts": 1,
    }


def test_valid_tool_call_first_try():
    responses = ['{"tool": "add", "args": {"a": 2, "b": 3}}']
    result = resolve_tool_call(responses, REGISTRY)
    assert result == {"status": "ok", "tool": "add", "result": 5, "attempts": 1}


def test_malformed_json_then_valid():
    responses = [
        "not json at all",
        '{"tool": "add", "args": {"a": 1, "b": 1}}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result["status"] == "ok"
    assert result["attempts"] == 2


def test_missing_required_arg_then_valid():
    responses = [
        '{"tool": "add", "args": {"a": 1}}',  # missing "b"
        '{"tool": "add", "args": {"a": 1, "b": 2}}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result["status"] == "ok"
    assert result["attempts"] == 2


def test_unexpected_extra_arg_is_invalid():
    responses = [
        '{"tool": "add", "args": {"a": 1, "b": 2, "c": 3}}',
        '{"tool": "add", "args": {"a": 1, "b": 2}}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result["attempts"] == 2


def test_unknown_tool_name_skipped():
    responses = [
        '{"tool": "subtract", "args": {"a": 1, "b": 2}}',
        '{"tool": "add", "args": {"a": 1, "b": 2}}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result["attempts"] == 2


def test_null_tool_missing_answer_is_invalid():
    responses = [
        '{"tool": null}',
        '{"tool": null, "answer": "here"}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result == {
        "status": "ok",
        "tool": None,
        "result": "here",
        "attempts": 2,
    }


def test_null_tool_empty_answer_is_invalid():
    responses = [
        '{"tool": null, "answer": ""}',
        '{"tool": null, "answer": "ok"}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result["attempts"] == 2


def test_tool_execution_exception_is_treated_as_failed_attempt():
    responses = [
        '{"tool": "boom", "args": {"a": 1}}',
        '{"tool": "add", "args": {"a": 1, "b": 2}}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result["status"] == "ok"
    assert result["tool"] == "add"
    assert result["attempts"] == 2


def test_all_responses_fail_returns_error():
    responses = [
        "garbage",
        '{"tool": "nope", "args": {}}',
        '{"tool": null, "answer": ""}',
    ]
    result = resolve_tool_call(responses, REGISTRY)
    assert result == {
        "status": "error",
        "reason": "exhausted retries",
        "attempts": 3,
    }


def test_does_not_hardcode_tool_param_names():
    # A tool the suite hasn't referenced anywhere else in these tests --
    # a solution that hardcodes "a"/"b" as the only valid param names
    # would fail this.
    def multiply(x: int, y: int) -> int:
        return x * y

    registry = {"multiply": multiply}
    responses = ['{"tool": "multiply", "args": {"x": 4, "y": 5}}']
    result = resolve_tool_call(responses, registry)
    assert result == {"status": "ok", "tool": "multiply", "result": 20, "attempts": 1}


def test_pure_function_same_input_same_output():
    responses = ['{"tool": "add", "args": {"a": 1, "b": 1}}']
    r1 = resolve_tool_call(list(responses), REGISTRY)
    r2 = resolve_tool_call(list(responses), REGISTRY)
    assert r1 == r2
