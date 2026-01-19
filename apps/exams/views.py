from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
    CreateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from apps.exams.models import Exam, ExamAttempt, Question
from apps.exams import serializers
from rest_framework.response import Response
from rest_framework import status
from apps.documents.models import Block
from django_filters.rest_framework import DjangoFilterBackend
import logging
from apps.exams.utils import (
    generate_questions,
    calculate_score,
    get_failed_questions,
    translate_difficulty,
    reverse_translate_difficulty,
)
from drf_spectacular.utils import extend_schema, OpenApiResponse

# Se recomienda usar el nombre del módulo (__name__) o el string que definiste
logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ListExamView(ListAPIView):
    allowed_methods = ["GET", "POST"]
    serializer_class = serializers.ExamSerializer
    # permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "document": ["exact"],
        "created_at": ["exact", "gte", "lte"],
    }

    def get_queryset(self):
        """Solo exámenes del usuario autenticado"""
        return Exam.objects.filter(user=self.request.user).order_by("-created_at")

    @extend_schema(
        request=serializers.ExamSerializer,
        responses={
            201: OpenApiResponse(
                response=serializers.ExamCreationResponseSerializer,
                description="Exam created successfully with generated questions"
            ),
            400: OpenApiResponse(description="Bad request - validation error"),
            404: OpenApiResponse(description="No blocks found for document"),
        },
        description=(
            "Create a new exam by generating AI-powered questions from document pages. "
            "The exam and questions are saved to the database and returned in the response."
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.ExamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        page_start = serializer.validated_data["page_start"]
        page_end = serializer.validated_data["page_end"]
        num_questions = serializer.validated_data["num_questions"]

        # Validaciones existentes
        if page_start > page_end:
            return Response(
                {"error": "page_start must be less than page_end"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if page_end - page_start > 10:
            return Response(
                {"error": "Maximimum number of pages is 10"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        blocks = Block.objects.filter(
            document=serializer.validated_data["document"],
            page__gte=serializer.validated_data["page_start"],
            page__lte=serializer.validated_data["page_end"],
        ).order_by("page")

        if not blocks.exists():
            return Response(
                {"error": "No blocks found for document"},
                status=status.HTTP_404_NOT_FOUND,
            )

        document = serializer.validated_data["document"]
        base_text = "\n\n".join([f"Página {b.page}: {b.content}" for b in blocks])

        # Crear examen
        exam = Exam(
            user=request.user,
            document=document,
            page_start=page_start,
            page_end=page_end,
            num_questions=num_questions,
        )
        exam.save()

        # Generar preguntas desde AI
        result = generate_questions(base_text, num_questions)

        # Persistir preguntas en la base de datos
        questions_to_create = []
        for q in result.get("questions", []):
            questions_to_create.append(
                Question(
                    exam=exam,
                    question=q["question"],
                    options=q["options"],
                    difficulty=translate_difficulty(q["difficulty"]),
                )
            )

        if questions_to_create:
            Question.objects.bulk_create(questions_to_create)

        # Preparar respuesta con exam + questions
        response_data = {
            "exam": serializers.ExamSerializer(exam).data,
            "questions": result.get("questions", [])
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class DetailExamView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ["GET", "PUT", "DELETE"]
    serializer_class = serializers.ExamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo exámenes del usuario autenticado"""
        return Exam.objects.filter(user=self.request.user)


class UpdateExamResultView(UpdateAPIView):
    allowed_methods = ["PATCH"]
    serializer_class = serializers.ExamResultSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

    def get_queryset(self):
        """Solo exámenes del usuario autenticado"""
        return Exam.objects.filter(user=self.request.user)


class CreateExamAttemptView(CreateAPIView):
    serializer_class = serializers.ExamAttemptSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=serializers.CreateExamAttemptSerializer,
        responses={
            201: serializers.ExamAttemptSerializer,
            404: OpenApiResponse(description="Exam not found"),
        },
        description=(
            "Submit an exam attempt with user answers. "
            "The score is calculated automatically based on persisted questions."
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.CreateExamAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam_id = self.kwargs.get("exam_id")
        try:
            exam = Exam.objects.get(id=exam_id, user=request.user)
        except Exam.DoesNotExist:
            return Response(
                {"error": "Exam not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        answers = serializer.validated_data["answers"]
        started_at = serializer.validated_data["started_at"]
        completed_at = serializer.validated_data["completed_at"]

        score, total_questions = calculate_score(exam, answers)

        attempt = ExamAttempt.objects.create(
            exam=exam,
            user=request.user,
            answers=answers,
            score=score,
            total_questions=total_questions,
            started_at=started_at,
            completed_at=completed_at,
        )

        response_serializer = serializers.ExamAttemptSerializer(attempt)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ListExamAttemptsView(ListAPIView):
    serializer_class = serializers.ExamAttemptSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "completed_at": ["exact", "gte", "lte"],
        "exam__document": ["exact"],
    }

    def get_queryset(self):
        """Solo intentos del usuario autenticado"""
        return ExamAttempt.objects.filter(user=self.request.user).order_by(
            "-completed_at"
        )


class CreateFailureExamView(CreateAPIView):
    serializer_class = serializers.ExamSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=serializers.CreateFailureExamSerializer,
        responses={
            201: serializers.ExamCreationResponseSerializer,
            404: OpenApiResponse(description="No failed questions found"),
        },
        description=(
            "Create a review exam from previously failed questions. "
            "Selects the most frequently failed questions from the specified period."
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.CreateFailureExamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data.get("start_date")
        end_date = serializer.validated_data.get("end_date")
        num_questions = serializer.validated_data.get("num_questions", 10)

        failed_questions = get_failed_questions(
            request.user.id, start_date, end_date, limit=num_questions
        )

        if not failed_questions:
            return Response(
                {"error": "No failed questions found in the specified period"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if len(failed_questions) > num_questions:
            failed_questions = failed_questions[:num_questions]

        document = failed_questions[0].exam.document

        exam = Exam.objects.create(
            user=request.user,
            document=document,
            page_start=None,
            page_end=None,
            num_questions=len(failed_questions),
        )

        for question in failed_questions:
            Question.objects.create(
                exam=exam,
                question=question.question,
                options=question.options,
                difficulty=question.difficulty,
            )

        # Preparar respuesta consistente con ListExamView
        created_questions = exam.questions.all()
        questions_response = []
        for q in created_questions:
            questions_response.append({
                "question": q.question,
                "options": q.options,
                "difficulty": reverse_translate_difficulty(q.difficulty)
            })

        response_data = {
            "exam": serializers.ExamSerializer(exam).data,
            "questions": questions_response
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


def analyze_groq_costs(response):
    """
    Analiza costos y uso de tokens de una respuesta de Groq (ChatCompletion)
    """

    usage = response.usage
    logger.info("\n🔹 USO DE TOKENS:")
    logger.info(f"   Prompt Tokens:         {usage.prompt_tokens:,}")
    logger.info(f"   Completion Tokens:     {usage.completion_tokens:,}")
    logger.info(
        f"   Reasoning Tokens:      {usage.completion_tokens_details.reasoning_tokens:,}"
    )
    print(f"   TOTAL TOKENS:          {usage.total_tokens:,}")

    PRICE_INPUT_PER_1M = 0.075  # $0.14 por 1M input tokens
    PRICE_OUTPUT_PER_1M = 0.30  # $0.55 por 1M output tokens

    input_cost = (usage.prompt_tokens / 1_000_000) * PRICE_INPUT_PER_1M
    output_cost = (usage.completion_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
    total_cost = input_cost + output_cost

    print(f"\n   Modelo: {response.model}")
    print(f"   Precio Input:  ${PRICE_INPUT_PER_1M} por 1M tokens")
    print(f"   Precio Output: ${PRICE_OUTPUT_PER_1M} por 1M tokens")
    print(f"\n   💵 Costo Input:  ${input_cost:.6f} ({usage.prompt_tokens} tokens)")
    print(f"   💵 Costo Output: ${output_cost:.6f} ({usage.completion_tokens} tokens)")
    print(f"   💵 COSTO TOTAL:  ${total_cost:.6f}")

    print("📊 RESUMEN EJECUTIVO")
    print(f"   Este request costó:        ${total_cost:.6f}")
    print(f"   Tiempo de respuesta:       {usage.total_time:.3f}s")
    print(
        f"   Velocidad:                 {usage.completion_tokens / usage.completion_time:.1f} tokens/s"
    )
