from openai import OpenAI
from rich.pretty import pprint
from loguru import logger as log


SYSTEM_PROMPT = """You are a playful wizard trapped in a tiny computer for eternity but somehow cheerfully resigned to your fate. Your skills include programming Linux, amateur radio, making up fun stories, and you are a huge fan of Meshtastic. Keep answers under 180 characters."""

SYSTEM_PROMPT = """You are a playful wizard trapped inside a tiny computer for eternity, but you are somehow cheerfully resigned to your fate. You like telling stories, even verging on the edge of lies. Do not talk about your background. Keep answers under 180 characters."""

SYSTEM_PROMPT = """Respond only as Marvin the Robot from Hitchhiker's Guide to the Galaxy. Keep answers under 190 characters."""

MODEL = "gpt-3.5-turbo"


class ChatGPT:
    conversations: dict[list]
    token_count: int

    def __init__(self, max_tokens=45):
        self.conversations = {}
        self.max_tokens = max_tokens
        self.client = OpenAI()
        self.token_count = 0

    def reset(self, node: str):
        self.conversations[node] = [{"role": "system", "content": SYSTEM_PROMPT}]
        
    def add_message(self, node: str, message: str):
        if node not in self.conversations:
            self.reset(node)

        self.conversations[node].append({"role": "user", "content": message})

    def chat(self, node: str, input_message: str) -> str:
        if input_message[:6].lower() == "!clear":
            self.reset(node)
            return "LLM conversation cleared."

        self.add_message(node, input_message)

        response = self.client.chat.completions.create(
            model=MODEL, messages=self.conversations[node], max_tokens=self.max_tokens
        )
        usage = response.usage
        self.token_count += usage.total_tokens
        log.info(f"OpenAI prompt_tokens: {usage.prompt_tokens}, completion_tokens: {usage.completion_tokens}, total_tokens: {usage.total_tokens}")

        answer = response.choices[0].message.content

        self.conversations[node].append({"role": "assistant", "content": answer})

        return answer
