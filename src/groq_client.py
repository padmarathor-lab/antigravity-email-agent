from groq import Groq
from src.config import Config
import time

def get_groq_client() -> Groq:
    """
    Initializes and returns the Groq API client.
    """
    Config.validate()
    return Groq(api_key=Config.GROQ_API_KEY)

def call_groq_with_retry(client: Groq, model: str, messages: list[dict], max_retries: int = 3, backoff_factor: int = 2) -> str:
    """
    Calls the Groq chat completion API with exponential backoff retries.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                raise e
            time.sleep(backoff_factor ** attempt)
