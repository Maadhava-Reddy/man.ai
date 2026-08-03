import os
import json
from openai import OpenAI

GITHUB_MODELS_URL = "https://models.github.ai/inference"


class ConversationManager:

    def __init__(self, system_prompt, model="gpt-4o-mini"):
        self.system_prompt = system_prompt
        self.model = model

        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

        openai_key = os.environ.get("OPENAI_API_KEY")
        github_key = os.environ.get("GITHUB_TOKEN")

        if openai_key:
            self.client = OpenAI(api_key=openai_key)
        elif github_key:
            self.client = OpenAI(base_url=GITHUB_MODELS_URL, api_key=github_key)
        else:
            raise ValueError("No API key found. Set OPENAI_API_KEY or GITHUB_TOKEN.")

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