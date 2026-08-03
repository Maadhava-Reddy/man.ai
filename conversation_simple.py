import os, json, re, types
from openai import OpenAI

class ConversationManager:

    def __init__(self, system_prompt):
        api_key = os.getenv("OPENAI_API_KEY") or "dummy-key-for-testing"
        self.client = OpenAI(api_key=api_key)
        self.messages = [{"role": "system", "content": system_prompt}]
        self.is_mock = False

    def ask(self, text, tools=None, functions=None):
        self.messages.append({"role": "user", "content": text})

        while True:
            if self.is_mock:
                response = self._mock_create(self.messages, tools)
            else:
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=self.messages,
                        tools=tools
                    )
                except Exception as e:
                    # Catch authentication/endpoint errors
                    if "401" in str(e) or "410" in str(e) or "invalid_api_key" in str(e) or (os.getenv("OPENAI_API_KEY") or "").startswith("github_pat_"):
                        print("\n[WARNING] Live API call failed due to invalid/retired API key. Falling back to offline Mock Mode.")
                        self.is_mock = True
                        response = self._mock_create(self.messages, tools)
                    else:
                        raise e

            msg = response.choices[0].message

            if msg.tool_calls:
                self.messages.append(msg)

                for call in msg.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments)
                    result = functions[name](**args)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": str(result)
                    })
            else:
                self.messages.append({"role": "assistant", "content": msg.content})
                return msg.content

    def _mock_create(self, messages, tools):
        # Find the last user message
        user_message = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                user_message = msg["content"]
                break
            elif not isinstance(msg, dict) and hasattr(msg, "role") and msg.role == "user":
                user_message = msg.content
                break
        
        # If the last message is from a tool, return the tool output processed message
        last_msg = messages[-1]
        is_tool = False
        tool_content = ""
        if isinstance(last_msg, dict) and last_msg.get("role") == "tool":
            is_tool = True
            tool_content = last_msg["content"]
        elif not isinstance(last_msg, dict) and hasattr(last_msg, "role") and last_msg.role == "tool":
            is_tool = True
            tool_content = last_msg.content

        if is_tool:
            content = f"Based on the tool output, here is the result: {tool_content}"
            return types.SimpleNamespace(choices=[
                types.SimpleNamespace(message=types.SimpleNamespace(content=content, tool_calls=None))
            ])
            
        user_lower = user_message.lower()
        
        # 1. Time query
        if any(w in user_lower for w in ["time", "date", "clock"]):
            call = types.SimpleNamespace(
                id="call_time_1",
                type="function",
                function=types.SimpleNamespace(name="get_current_time", arguments="{}")
            )
            return types.SimpleNamespace(choices=[
                types.SimpleNamespace(message=types.SimpleNamespace(content=None, tool_calls=[call]))
            ])
            
        # 2. Arithmetic expression query
        math_match = re.search(r'([0-9\s\+\-\*\/\(\)\.]+)', user_message)
        if math_match and any(op in math_match.group(1) for op in ["+", "-", "*", "/"]):
            expression = math_match.group(1).strip()
            call = types.SimpleNamespace(
                id="call_calc_1",
                type="function",
                function=types.SimpleNamespace(name="calculate", arguments=json.dumps({"expression": expression}))
            )
            return types.SimpleNamespace(choices=[
                types.SimpleNamespace(message=types.SimpleNamespace(content=None, tool_calls=[call]))
            ])
            
        # 3. File query
        if any(w in user_lower for w in ["read", "file", "contents"]):
            path_match = re.search(r'([\w\-\.\/\\:]+\.\w+)', user_message)
            path = path_match.group(1) if path_match else "requirements.txt"
            call = types.SimpleNamespace(
                id="call_file_1",
                type="function",
                function=types.SimpleNamespace(name="read_text_file", arguments=json.dumps({"path": path}))
            )
            return types.SimpleNamespace(choices=[
                types.SimpleNamespace(message=types.SimpleNamespace(content=None, tool_calls=[call]))
            ])
            
        # 4. Standard conversational response
        content = f"Hello! (Running in Mock Mode) You said: '{user_message}'. To run in Live Mode, please configure a valid OPENAI_API_KEY in your .env file."
        return types.SimpleNamespace(choices=[
            types.SimpleNamespace(message=types.SimpleNamespace(content=content, tool_calls=None))
        ])

    def clear(self):
        self.messages = [self.messages[0]]