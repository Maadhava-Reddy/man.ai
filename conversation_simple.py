import os
import json
import re
import types
from openai import OpenAI

class MockChoice:
    def __init__(self, message):
        self.message = message

class MockResponse:
    def __init__(self, choices):
        self.choices = choices

class MockToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.type = "function"
        self.function = types.SimpleNamespace(name=name, arguments=json.dumps(arguments))

class MockCompletions:
    def create(self, model, messages, tools=None, **kwargs):
        # Find the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        # If the last message is from a tool, return the tool output processed message
        last_msg = messages[-1]
        if last_msg["role"] == "tool":
            tool_content = last_msg["content"]
            content = f"Based on the tool output, here is the result: {tool_content}"
            return MockResponse([MockChoice(types.SimpleNamespace(content=content, tool_calls=None))])
            
        user_lower = user_message.lower()
        
        # 1. Time query
        if any(w in user_lower for w in ["time", "date", "clock"]):
            tool_call = MockToolCall("call_time_1", "get_current_time", {})
            return MockResponse([MockChoice(types.SimpleNamespace(content=None, tool_calls=[tool_call]))])
            
        # 2. Arithmetic expression query
        math_match = re.search(r'([0-9\s\+\-\*\/\(\)\.]+)', user_message)
        if math_match and any(op in math_match.group(1) for op in ["+", "-", "*", "/"]):
            expression = math_match.group(1).strip()
            tool_call = MockToolCall("call_calc_1", "calculate", {"expression": expression})
            return MockResponse([MockChoice(types.SimpleNamespace(content=None, tool_calls=[tool_call]))])
            
        # 3. File query
        if any(w in user_lower for w in ["read", "file", "contents"]):
            path_match = re.search(r'([\w\-\.\/\\:]+\.\w+)', user_message)
            path = path_match.group(1) if path_match else "requirements.txt"
            tool_call = MockToolCall("call_file_1", "read_text_file", {"path": path})
            return MockResponse([MockChoice(types.SimpleNamespace(content=None, tool_calls=[tool_call]))])
            
        # 4. Standard conversational response
        content = f"Hello! (Running in Mock Mode) You said: '{user_message}'. To use the real LLM, please configure a valid OPENAI_API_KEY in your .env file."
        return MockResponse([MockChoice(types.SimpleNamespace(content=content, tool_calls=None))])

class MockClient:
    def __init__(self):
        self.chat = types.SimpleNamespace(completions=MockCompletions())


class ConversationManager:

    def __init__(self, system_prompt, model="gpt-4o-mini", force_mock=False):
        self.system_prompt = system_prompt
        self.model = model
        self.is_mock = force_mock

        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

        if force_mock:
            self.client = MockClient()
            return

        openai_key = os.environ.get("OPENAI_API_KEY")

        if openai_key:
            self.client = OpenAI(api_key=openai_key)
        else:
            print("\n[WARNING] No OPENAI_API_KEY found or GITHUB_TOKEN has been retired. Falling back to local offline Mock Mode.")
            self.is_mock = True
            self.client = MockClient()

    def add_user_message(self, text):
        self.messages.append({"role": "user", "content": text})

    def ask(self, user_text):
        self.add_user_message(user_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )

        reply_text = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply_text})
        return reply_text

    def clear(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def ask_with_tools(self, user_text, tools, tool_functions):
        self.add_user_message(user_text)

        max_tries = 5

        for attempt in range(max_tries):

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=tools
            )

            reply = response.choices[0].message

            if reply.tool_calls:
                self._handle_tool_calls(reply, tool_functions)
                continue

            self.messages.append({"role": "assistant", "content": reply.content})
            return reply.content

        return "Sorry, I couldn't finish after several tool calls."

    def _handle_tool_calls(self, reply, tool_functions):
        self.messages.append({
            "role": "assistant",
            "content": reply.content,
            "tool_calls": reply.tool_calls
        })

        for call in reply.tool_calls:
            tool_name = call.function.name
            tool_args = json.loads(call.function.arguments or "{}")

            result = self._run_one_tool(tool_name, tool_args, tool_functions)

            self.messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result)
            })

    def _run_one_tool(self, name, args, tool_functions):
        function_to_call = tool_functions.get(name)

        if function_to_call is None:
            return f"Error: I don't have a tool called '{name}'"

        try:
            return function_to_call(**args)
        except Exception as e:
            return f"Error while running '{name}': {e}"