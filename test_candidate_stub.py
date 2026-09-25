import pytest
from candidate_stub import resolve_tool_call

class TestCandidateSuite:
    def test_llm_gave_a_direct_answer_no_tool_needed_return_answer(self):
        responses = ['{"tool": null, "answer": "Paris is the capital of France."}']

        result = resolve_tool_call(responses, responses)

        assert result == {
            "status": "ok",
            "tool": None,
            "result": "Paris is the capital of France.",
            "attempts": 1,
        }