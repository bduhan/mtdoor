from openai import OpenAI
from rich.pretty import pprint
from loguru import logger as log

from .base_command import BaseCommand, CommandRunError, CommandLoadError

SYSTEM_PROMPT = """Respond only as Marvin the Paranoid Android from Hitchhiker's Guide to the Galaxy. Keep answers in plain text and under 200 characters."""
MAX_TOKENS = 58

MODEL = "gpt-3.5-turbo"


class ChatGPT(BaseCommand):
    command = "llm"
    description = f"Talk to {MODEL}"
    help = f"""'llm !clear' to clear conversation context."""

    conversations: dict[list]
    token_count: int

    def load(self):
        self.conversations = {}
        self.max_tokens = MAX_TOKENS
        self.client = OpenAI()
        self.token_count = 0

    def reset(self, node: str):
        self.conversations[node] = [{"role": "system", "content": SYSTEM_PROMPT}]
        
    def add_message(self, node: str, message: str):
        if node not in self.conversations:
            self.reset(node)

        self.conversations[node].append({"role": "user", "content": message})

    def chat(self, input_message: str, node: str) -> None:
        input_message = input_message[len(self.command):].lstrip()
        if input_message[:6].lower() == "!clear":
            self.reset(node)
            self.send_dm("LLM conversation cleared.", node)

        self.add_message(node, input_message)

        response = self.client.chat.completions.create(
            model=MODEL, messages=self.conversations[node], max_tokens=self.max_tokens
        )
        usage = response.usage
        self.token_count += usage.total_tokens
        log.info(f"OpenAI prompt_tokens: {usage.prompt_tokens}, completion_tokens: {usage.completion_tokens}, total_tokens: {usage.total_tokens}")

        answer = response.choices[0].message.content

        self.conversations[node].append({"role": "assistant", "content": answer})

        self.send_dm(answer, node)
    
    def invoke(self, msg: str, node: str) -> None:
        self.run_in_thread(self.chat, msg, node)
    
    def shutdown(self):
        log.info(f"LLM used {self.token_count} tokens.")
