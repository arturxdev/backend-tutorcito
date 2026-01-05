from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from apps.exams.models import Exam
from apps.exams import serializers
from rest_framework.response import Response
from rest_framework import status
from apps.documents.models import Block
from django_filters.rest_framework import DjangoFilterBackend
import logging
from apps.exams.utils import generate_questions

# Se recomienda usar el nombre del módulo (__name__) o el string que definiste
logger = logging.getLogger(__name__)


class ListExamView(ListAPIView):
    allowed_methods = ["GET", "POST"]
    serializer_class = serializers.ExamSerializer
    # permission_classes = [IsAuthenticated]
    filterset_fields = ["document"]

    def get_queryset(self):
        """Solo exámenes del usuario autenticado"""
        return Exam.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        serializer = serializers.ExamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        page_start = serializer.validated_data["page_start"]
        page_end = serializer.validated_data["page_end"]
        num_questions = serializer.validated_data["num_questions"]
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
        exam = Exam(
            user=request.user,
            document=document,
            page_start=page_start,
            page_end=page_end,
            num_questions=num_questions,
        )
        exam.save()
        result = generate_questions(base_text, num_questions)
        return Response(result, status=status.HTTP_201_CREATED)


class DetailExamView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ["GET", "PUT", "DELETE"]
    serializer_class = serializers.ExamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo exámenes del usuario autenticado"""
        return Exam.objects.filter(user=self.request.user)


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
