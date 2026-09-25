# Mock interview question: Tool-call resolution with retries

**Level:** mid-level backend / AI engineering
**Topic:** deterministic dispatch on top of a probabilistic LLM (same theme as our conversation)
**Time box:** ~25–30 minutes

## Context

You're building the piece of an LLM app that sits between the model's raw
output and your tool-execution code (the same role `route` / `run_tool`
played in the LangGraph examples). Because the model is sampled, it doesn't
always return valid, well-formed tool calls on the first try — your app
retries by asking the model again, and you end up with an ordered list of
attempts. You need one function that walks that list and resolves it to a
final result deterministically.

## Task

Implement:

```python
def resolve_tool_call(responses: list[str], registry: dict) -> dict:
    ...
```

- `responses` — an ordered list of raw strings, each one a candidate LLM
  reply (simulating successive retries). Try them **in order**; stop at the
  first one that resolves successfully.
- `registry` — a dict mapping tool name (str) → callable.

Each response string is expected to be JSON shaped like one of:

```json
{"tool": null, "answer": "some direct answer"}
{"tool": "tool_name", "args": {"a": 1, "b": 2}}
```

A response counts as **valid** only if *all* of the following hold:

1. It parses as JSON and the result is a `dict`.
2. It has a `"tool"` key.
3. If `"tool"` is `null` → it also has an `"answer"` key whose value is a
   non-empty string.
4. If `"tool"` is a string → it also has an `"args"` key that is a `dict`,
   the tool name exists in `registry`, and the keys in `"args"` **exactly**
   match the callable's parameters (no missing params, no unexpected extras).
5. If the tool call is otherwise valid but calling the function raises an
   exception, that counts as a **failed attempt** too (not a crash) — move
   on to the next response.

Return value:

- On success with a direct answer:
  `{"status": "ok", "tool": None, "result": <answer str>, "attempts": N}`
- On success calling a tool:
  `{"status": "ok", "tool": <name>, "result": <return value>, "attempts": N}`
- If every response in the list fails:
  `{"status": "error", "reason": "exhausted retries", "attempts": len(responses)}`

`attempts` is always the 1-indexed position of the response that succeeded
(or `len(responses)` on total failure).

## What good looks like

A strong answer will:
- Use `inspect.signature` (or equivalent) rather than hardcoding param names
  per tool — the function shouldn't need to know about `calculate_tip` or
  `get_order_status` specifically.
- Cleanly separate three failure categories: malformed JSON, schema
  mismatch, and runtime exception from the tool itself — and treat all
  three as "try the next response" rather than crashing the caller.
- Not mutate or depend on ordering side effects across calls (pure
  function, safe to call repeatedly with the same inputs → same output).

## How to grade it

Run the test suite in `test_resolve_tool_call.py` against the candidate's
implementation:

```bash
pytest test_resolve_tool_call.py -v
```

All tests passing is close to a hire signal on correctness; watch during
the interview for whether they reach for `inspect.signature` themselves or
need a nudge, and how they reason about which failures should retry vs.
raise.
