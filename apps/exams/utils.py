from django.conf import settings
from groq import Groq
import json
import uuid
from collections import Counter

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

    result = json.loads(response.choices[0].message.content or "{}")

    for question in result.get("questions", []):
        for option in question.get("options", []):
            if "id" not in option:
                option["id"] = str(uuid.uuid4())

    return result


def calculate_score(exam, answers):
    correct = 0
    for question in exam.questions.all():
        selected_option_id = answers.get(str(question.id))
        if not selected_option_id:
            continue

        for option in question.options:
            if option["id"] == selected_option_id and option["isCorrect"]:
                correct += 1
                break

    total = exam.questions.count()
    return correct, total


def get_failed_questions(user_id, start_date, end_date, limit=20):
    from apps.exams.models import ExamAttempt

    attempts = (
        ExamAttempt.objects.filter(
            user_id=user_id, completed_at__gte=start_date, completed_at__lte=end_date
        )
        .select_related("exam")
        .prefetch_related("exam__questions")
    )

    failed_counter = Counter()

    for attempt in attempts:
        for question in attempt.exam.questions.all():
            selected_option_id = attempt.answers.get(str(question.id))
            if not selected_option_id:
                failed_counter[question] += 1
                continue

            is_correct = any(
                opt["id"] == selected_option_id and opt["isCorrect"]
                for opt in question.options
            )

            if not is_correct:
                failed_counter[question] += 1

    most_failed = failed_counter.most_common(limit)
    return [question for question, count in most_failed]


def translate_difficulty(english_difficulty: str) -> str:
    """
    Translates English difficulty levels from AI to Spanish database values.

    Args:
        english_difficulty: "easy", "medium", or "hard"

    Returns:
        Spanish difficulty: "facil", "medio", or "dificil"
    """
    difficulty_map = {
        "easy": "facil",
        "medium": "medio",
        "hard": "dificil",
    }
    return difficulty_map.get(english_difficulty, "medio")


def reverse_translate_difficulty(spanish_difficulty: str) -> str:
    """
    Translates Spanish database difficulty to English API response format.

    Args:
        spanish_difficulty: "facil", "medio", or "dificil"

    Returns:
        English difficulty: "easy", "medium", or "hard"
    """
    difficulty_map = {
        "facil": "easy",
        "medio": "medium",
        "dificil": "hard",
    }
    return difficulty_map.get(spanish_difficulty, "medium")
