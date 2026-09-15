import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List
from groq import Groq

load_dotenv()

class Issue(BaseModel):
    type: str
    line: int
    severity: str
    description: str
    reason: str
    suggested_fix: str

class IssuesResponse(BaseModel):
    issues: List[Issue]

class FixedCode(BaseModel):
    code: str

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_llm(prompt):   
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"Error Generating: {e}"

def generate_chat(prompt):
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

    except Exception as e:
        raise RuntimeError(f"Groq chat failed: {e}")

def generate_lang(prompt):
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

        raw = response.choices[0].message.content

        parsed = IssuesResponse.model_validate_json(raw)

        return [
            issue.model_dump()
            for issue in parsed.issues
        ]

    except Exception as e:
        raise RuntimeError(f"LLM analysis failed: {e}")
    
def generate_code(prompt):

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FixedCode
            )
        )

        return response.parsed.code

    except Exception as e:
        raise RuntimeError(f"Code generation failed: {e}")