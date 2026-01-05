from django.conf import settings
from groq import Groq
import json

groq = Groq(
    api_key=settings.GROQ_API_KEY,
)

PROMPT = """
Genera {num_questions} preguntas apartir de este texto que te de el usuario.
las preguntas deben de estar generadas en espanol y cada pregunta debe de tener 4 opciones, una correcta y 3 incorrectas.
"""


def generate_questions(base_text, num_questions):
    response = groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": PROMPT.format(num_questions=num_questions),
            },
            {
                "role": "user",
                "content": base_text,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "multiple_choice_questions",
                "strict": True,
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["questions"],
                    "additionalProperties": False,
                    "properties": {
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["question", "options", "difficulty"],
                                "additionalProperties": False,
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "Enunciado de la pregunta.",
                                    },
                                    "options": {
                                        "type": "array",
                                        "minItems": 1,
                                        "items": {
                                            "type": "object",
                                            "required": ["text", "isCorrect"],
                                            "additionalProperties": False,
                                            "properties": {
                                                "text": {
                                                    "type": "string",
                                                    "description": "Texto de la opción de respuesta.",
                                                },
                                                "isCorrect": {
                                                    "type": "boolean",
                                                    "description": "Indica si esta opción es la correcta.",
                                                },
                                            },
                                        },
                                    },
                                    "difficulty": {
                                        "type": "string",
                                        "enum": ["easy", "medium", "hard"],
                                        "description": "Nivel de dificultad de la pregunta.",
                                    },
                                },
                            },
                        }
                    },
                },
            },
        },
    )

    return json.loads(response.choices[0].message.content or "{}")
