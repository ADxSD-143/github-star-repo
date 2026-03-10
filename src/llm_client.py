import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        self.client = OpenAI(**kwargs)
        self.model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

    def analyze_action(self, system_prompt: str, ocr_context: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the OCR text:\n\n{ocr_context}"}
                ],
                temperature=0.1
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error during LLM analysis: {e}")
            return f"Error: {e}"