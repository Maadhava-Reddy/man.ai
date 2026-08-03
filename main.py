import os
from dotenv import load_dotenv
from conversation_simple import ConversationManager
from tools import TOOL_SCHEMAS, TOOL_REGISTRY

# Load environment variables from a local .env file if present
load_dotenv()

def main():
    print("Initializing Conversation Manager...")
    try:
        convo = ConversationManager(
            system_prompt="You are a helpful assistant with access to local tools (calculator, clock, and file reader)."
        )
    except ValueError as e:
        print(f"\nError: {e}")
        print("Please set the OPENAI_API_KEY or GITHUB_TOKEN environment variable.")
        print("You can create a '.env' file in this folder and add: OPENAI_API_KEY=your_key_here")
        return

    print("\nAgent is ready! Type 'exit' or 'quit' to quit.")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.strip().lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if not user_input.strip():
                continue
                
            print("Thinking...")
            reply = convo.ask_with_tools(
                user_input,
                tools=TOOL_SCHEMAS,
                tool_functions=TOOL_REGISTRY
            )
            print(f"\nAgent: {reply}")
            print("-" * 50)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
