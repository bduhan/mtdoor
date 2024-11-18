import os
from openai import OpenAI
from loguru import logger as log

from . import BaseCommand, CommandLoadError


class ChatGPT(BaseCommand):
    command = "llm"
    description = f"Talk to a Large Language Model (ChatGPT)"
    help = f"""'llm !clear' to clear conversation context."""

    conversations: dict[list]
    token_count: int

    def load(self):
        self.conversations = {}
        self.max_tokens = self.get_setting(int, "max_tokens", 50)
        self.system_prompt = (
            self.get_setting(str, "system_prompt", "").strip('"').strip("'")
        )
        self.model = self.get_setting(str, "model", "gpt-3.5-turbo")
        self.api_key = self.get_setting(str, "api_key", os.getenv("OPENAI_API_KEY"))
        if not self.api_key:
            log.warning(
                "Set api_key in config.ini or set OPENAI_API_KEY environment variable."
            )
            raise CommandLoadError(f"{self.command} missing configuration data")

        self.client = OpenAI(api_key=self.api_key)
        self.token_count = 0

    def reset(self, node: str):
        self.conversations[node] = [{"role": "system", "content": self.system_prompt}]

    def add_message(self, node: str, message: str):
        if node not in self.conversations:
            self.reset(node)

        self.conversations[node].append({"role": "user", "content": message})

    def chat(self, input_message: str, node: str) -> None:
        input_message = input_message[len(self.command) :].lstrip()
        if input_message[:6].lower() == "!clear":
            self.reset(node)
            self.send_dm("LLM conversation cleared.", node)
            return

        self.add_message(node, input_message)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversations[node],
            max_tokens=self.max_tokens,
        )
        usage = response.usage
        self.token_count += usage.total_tokens
        log.info(
            f"OpenAI prompt_tokens: {usage.prompt_tokens}, completion_tokens: {usage.completion_tokens}, total_tokens: {usage.total_tokens}"
        )

        answer = response.choices[0].message.content[:200]

        self.conversations[node].append({"role": "assistant", "content": answer})

        self.send_dm(answer, node)

    def invoke(self, msg: str, node: str) -> None:
        self.run_in_thread(self.chat, msg, node)

    def shutdown(self):
        log.info(f"LLM used {self.token_count} tokens.")
