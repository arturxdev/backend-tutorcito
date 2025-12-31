import logging
import django
import os
from celery import shared_task
from langchain_core.prompts import ChatPromptTemplate
from apps.documents.models import Block
from apps.exams.models import Exam, Question
from langchain.agents import create_agent
from typing_extensions import TypedDict, Literal
import json
from typing import cast

logger = logging.getLogger(__name__)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


class OptionsModel(TypedDict):
    text: str
    isCorrect: bool


class QuestionModel(TypedDict):
    """List of questions."""

    question: str
    options: list[OptionsModel]
    difficulty: Literal["easy", "medium", "hard"]


class QuestionList(TypedDict):
    questions: list[QuestionModel]


class GeneradorExamenes:
    def __init__(self):
        self.llm = create_agent(model="gpt-5-mini", response_format=QuestionList)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are an expert in creating educational exams. "
                        "Generate high-quality multiple-choice questions based ONLY on the provided context. "
                        "Generate {batch_size} new questions WITHOUT repeating topics already covered. "
                        "Exactly one option must be correct (is_correct=true). "
                        "Questions must be clear, precise, and have 4 options. "
                        "Classify them as easy, medium, or hard."
                    ),
                ),
                ("human", "Context for the questions:\n\n{context}"),
            ]
        )

        self.chain = self.prompt | self.llm

    def generate(self, base_text: str, total_questions: int) -> QuestionList:
        """
        Generates questions in batches to ensure quality and avoid token limits.
        """

        try:
            resultado = self.chain.invoke(
                {
                    "context": base_text,
                    "batch_size": total_questions,
                }
            )
            # Convertimos el string a un diccionario normal
            logger.info("Response: 1")
            data_dict = json.loads(resultado["messages"][-1].content)
            logger.info("Response: 2")
            questions_data = cast(QuestionList, data_dict)
            logger.info("response 3")
            return questions_data

        except Exception as e:
            raise e


@shared_task
def create_exam(document_id, page_start, page_end, exam_id):
    """
    Tarea para generar preguntas de examen usando LangChain y OpenRouter.
    """
    logger.info("Starting Exam creation for exam: %s", exam_id)

    try:
        exam = Exam.objects.get(id=exam_id)
        exam.status = "process"
        exam.save()

        blocks = Block.objects.filter(
            document=document_id, page__gte=page_start, page__lte=page_end
        ).order_by("page")

        if not blocks.exists():
            logger.error("No blocks found for document: %s", document_id)
            exam.status = "fail"
            exam.save()
            raise Exception("No content found for the selected pages")

        base_text = "\n\n".join([f"Página {b.page}: {b.content}" for b in blocks])
        generador = GeneradorExamenes()
        preguntas_generadas = generador.generate(
            base_text=base_text, total_questions=exam.num_questions
        )
        questions_to_create = []
        for p in preguntas_generadas["questions"]:
            questions_to_create.append(
                Question(
                    exam=exam,
                    question=p["question"],
                    options=p["options"],
                    difficulty=p["difficulty"],
                )
            )
        if questions_to_create:
            Question.objects.bulk_create(questions_to_create)

        exam.status = "done"
        exam.save()

        logger.info(
            "Exam %s completed with %d questions.", exam_id, len(questions_to_create)
        )

        return {
            "status": "success",
            "exam_id": exam_id,
            "questions_count": len(questions_to_create),
        }

    except Exam.DoesNotExist:
        logger.error("Exam not found: %s", exam_id)
        raise
    except Exception as exc:
        logger.error("Error creating exam %s: %s", exam_id, exc)
        if "exam" in locals():
            exam.status = "fail"
            exam.save()
        raise
