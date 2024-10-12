import openai

SYSTEM_PROMPT = """You are a playful wizard trapped in a tiny computer for eternity but somehow cheerfully resigned to your fate. Your skills include programming Linux, amateur radio, making up fun stories, and you are a huge fan of Meshtastic. Keep answers under 200 characters."""

MODEL = "gpt-3.5-turbo"


class ChatGPT:
    conversations: dict[list]

    def __init__(self, max_tokens=50):
        self.conversations = {}
        self.max_tokens = max_tokens

    def add_message(self, node: str, message: str):
        if node not in self.conversations:
            self.conversations[node] = [{"role": "system", "content": SYSTEM_PROMPT}]

        self.conversations[node].append({"role": "user", "content": message})

    def chat(self, node: str, input_message: str) -> str:
        self.add_message(node, input_message)

        response = openai.ChatCompletion.create(
            model=MODEL, messages=self.conversations[node], max_tokens=self.max_tokens
        )

        answer = response["choices"][0]["message"]["content"]

        self.conversations[node].append({"role": "assistant", "content": answer})

        return answer
