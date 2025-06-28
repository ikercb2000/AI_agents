# project modules

from src.secretario_bot.enums import llm_models

# packages

from llama_cpp import Llama
import time

# LLM Bot


class LLMMessageGenerator:
    def __init__(self, model: llm_models):
        """
        Initializes the LLMMessageGenerator with the provided model path.
        """
        self.model = Llama.from_pretrained(repo_id=self.model_repo(model), filename=self.model_path(
            model), verbose=False, max_tokens=600, temperature=0.7)

    def generate_message(self, prompt: str) -> str:
        """
        Generates a message based on the provided prompt using the LLM model.
        """
        t0 = time.perf_counter()
        response = self.model(prompt, max_tokens=600, temperature=0.7)
        elapsed = time.perf_counter() - t0
        text = response['choices'][0]['text'].strip()
        print(f"RESPONSE ({elapsed:.2f}s)", flush=True)
        return text

    @staticmethod
    def model_repo(model: llm_models) -> str:
        """
        Returns the model repository based on the selected LLM model.
        """
        if model == llm_models.mistral_7b:
            return "TheBloke/Mistral-7B-Instruct-v0.1-GGUF"
        else:
            raise ValueError("Invalid LLM model selected.")

    @staticmethod
    def model_path(model: llm_models) -> str:
        """
        Returns the model path based on the selected LLM model.
        """
        if model == llm_models.mistral_7b:
            return "mistral-7b-instruct-v0.1.Q8_0.gguf"
        else:
            raise ValueError("Invalid LLM model selected.")
