import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    project, location = os.getenv("GCP_PROJECT"), os.getenv("VERTEX_REGION")
    if not project or not location:
        raise ValueError("GCP_PROJECT and VERTEX_REGION must be set")
    return genai.Client(vertexai=True, project=project, location=location)


def generate(prompt: str, temperature: float = 0.2) -> str:
    model = os.getenv("GEMINI_MODEL")
    if not model:
        raise ValueError("GEMINI_MODEL must be set")
    response = get_client().models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response")
    return response.text