
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

PROJECT_ID = os.getenv("GCP_PROJECT")
LOCATION = os.getenv("VERTEX_REGION")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

if not PROJECT_ID or not LOCATION or not GEMINI_MODEL:
    raise ValueError("Missing required GCP or Gemini environment variables.")

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)


def generate(prompt: str) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text
