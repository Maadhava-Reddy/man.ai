import os, json
from openai import OpenAI

class ConversationManager:

    def __init__(self, system_prompt):
        api_key = os.getenv("OPENAI_API_KEY") or "dummy-key-for-testing"
        self.client = OpenAI(api_key=api_key)
        self.messages = [{"role": "system", "content": system_prompt}]

    def ask(self, text, tools=None, functions=None):
        self.messages.append({"role": "user", "content": text})

        while True:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                tools=tools
            )

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

    def clear(self):
        self.messages = [self.messages[0]]