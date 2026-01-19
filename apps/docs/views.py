from django.http import HttpResponse
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.conf import settings
from drf_spectacular.generators import SchemaGenerator

from .llms_generator import LLMsTextGenerator


class LLMsTextView(View):
    """Returns LLM-optimized API documentation in plain text."""

    def dispatch(self, request, *args, **kwargs):
        # Cache 15 min only in production
        if not settings.DEBUG:
            self.get = method_decorator(cache_page(60 * 15))(self.get)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        base_url = request.build_absolute_uri("/api")

        llms_generator = LLMsTextGenerator(schema, base_url)
        content = llms_generator.generate()

        return HttpResponse(content, content_type="text/plain; charset=utf-8")
