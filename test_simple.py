
import json
import os
import types

os.environ.setdefault("GITHUB_TOKEN", "dummy-not-used-fake-client-only")

from conversation_simple import ConversationManager
from tools import TOOL_SCHEMAS, TOOL_REGISTRY


# ---- fake LLM pieces, just for testing ----

class FakeCall:
    def __init__(self, name, args):
        self.id = "call_1"
        self.function = types.SimpleNamespace(name=name, arguments=json.dumps(args))


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


def fake_create(model, messages, tools=None, _state={"count": 0}):
    _state["count"] += 1
    if _state["count"] == 1:
        call = FakeCall("calculate", {"expression": "12 * 4"})
        return types.SimpleNamespace(choices=[types.SimpleNamespace(
            message=FakeMessage(content=None, tool_calls=[call])
        )])
    return types.SimpleNamespace(choices=[types.SimpleNamespace(
        message=FakeMessage(content="12 * 4 is 48.", tool_calls=None)
    )])


# ---- run it ----

if __name__ == "__main__":
    convo = ConversationManager(system_prompt="You are a helpful assistant.")

    # swap in our fake client so no real API call happens
    convo.client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(create=fake_create)
        )
    )

    answer = convo.ask_with_tools(
        "What is 12 times 4?",
        tools=TOOL_SCHEMAS,
        tool_functions=TOOL_REGISTRY
    )

    print("Answer:", answer)
    assert "48" in answer
    print("It works! The tool was called and the result was used in the answer.")
