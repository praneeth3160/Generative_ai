import json
import os

from dotenv import load_dotenv
from google import genai
from google.api_core.exceptions import GoogleAPIError
from google.generativeai import types
from google.generativeai.types.generation_types import ResponseValidationError
from groq import Groq, APIError as GroqAPIError
from pydantic import BaseModel, ValidationError

load_dotenv()

class Issue(BaseModel):
    type: str
    line: int
    severity: str
    description: str
    reason: str
    suggested_fix: str

class IssuesResponse(BaseModel):
    issues: list[Issue]

class FixedCode(BaseModel):
    code: str

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_llm(prompt: str) -> str:
    """
    Generates text using the Gemini LLM.

    Args:
        prompt: The input prompt string.
                Callers should sanitize this prompt if necessary.

    Returns:
        The generated text from the LLM.

    Raises:
        RuntimeError: If there is an error generating content from the LLM.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text

    except GoogleAPIError as e:
        raise RuntimeError(f"LLM generation failed due to API error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during LLM generation: {e}") from e

def generate_chat(prompt: str) -> str:
    """
    Generates chat responses using the Groq LLM.

    Args:
        prompt: The input prompt string.
                Callers should sanitize this prompt if necessary.

    Returns:
        The generated chat message content.

    Raises:
        RuntimeError: If the Groq chat completion fails.
    """
    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except GroqAPIError as e:
        raise RuntimeError(f"Groq chat failed due to API error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during Groq chat completion: {e}") from e

def generate_lang(prompt: str) -> list[dict]:
    """
    Analyzes code/issues using the Groq LLM and returns structured analysis.

    Args:
        prompt: The input prompt string, which includes specific JSON format instructions.
                Callers should sanitize this prompt if necessary.

    Returns:
        A list of dictionaries, where each dictionary represents an issue
        conforming to the `Issue` schema.

    Raises:
        RuntimeError: If the LLM analysis fails due to API errors,
                      malformed JSON output, or schema validation issues.
    """
    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt + """
IMPORTANT: Every object inside the "issues" array MUST contain ALL SIX fields:

1. type
2. line
3. severity
4. description
5. reason
6. suggested_fix

"suggested_fix" is REQUIRED even when you think there is no fix.
If no specific fix is needed, use:
"suggested_fix": "No fix required."

Return ONLY valid JSON.

The exact structure is:

{
    "issues": [
        {
            "type": "string",
            "line": 0,
            "severity": "string",
            "description": "string",
            "reason": "string",
            "suggested_fix": "string"
        }
    ]
}

If there are no issues, return:

{
    "issues": []
}

Do not omit any field from an issue.
Do not add any fields.
Do not return Markdown.
Do not return explanations outside the JSON.
"""
                }
            ],
            response_format={"type": "json_object"},
            reasoning_effort="low",
            max_completion_tokens=8192
        )

        raw_content = response.choices[0].message.content

        try:
            parsed = IssuesResponse.model_validate_json(raw_content)
        except ValidationError as ve:
            raise RuntimeError(f"LLM analysis failed: JSON output violates schema. Raw: {raw_content}. Error: {ve}") from ve
        except json.JSONDecodeError as jde:
            raise RuntimeError(f"LLM analysis failed: Malformed JSON output. Raw: {raw_content}. Error: {jde}") from jde

        return [
            issue.model_dump()
            for issue in parsed.issues
        ]

    except GroqAPIError as e:
        raise RuntimeError(f"LLM analysis failed due to Groq API error: {e}") from e
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during LLM analysis: {e}") from e
    
def generate_code(prompt: str) -> str:
    """
    Generates code fixes using the Gemini LLM, returning code in a structured format.

    Args:
        prompt: The input prompt string describing the code to fix and context.
                Callers should sanitize this prompt if necessary.

    Returns:
        The generated fixed code as a string.

    Raises:
        RuntimeError: If code generation fails due to API errors,
                      invalid LLM output, or schema validation issues.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FixedCode
            )
        )

        if response.parsed is None:
            raise RuntimeError("Code generation failed: LLM returned no parsed content.")
        if not isinstance(response.parsed, FixedCode):
            raise TypeError(f"Code generation failed: LLM parsed content is not a FixedCode object. Type: {type(response.parsed)}")

        return response.parsed.code

    except GoogleAPIError as e:
        raise RuntimeError(f"Code generation failed due to API error: {e}") from e
    except ResponseValidationError as e:
        raise RuntimeError(f"Code generation failed: LLM output violates schema. Error: {e}") from e
    except AttributeError as e:
        raise RuntimeError(f"Code generation failed: Unexpected response structure from LLM. Missing attribute: {e}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during code generation: {e}") from e