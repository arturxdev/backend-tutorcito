# AGENTS.md

This file contains guidelines and commands for AI agents working in this Django project.

## Build, Lint, and Test Commands

```bash
python manage.py test                              # Run all tests
python manage.py test apps.documents.tests        # Single test class
python manage.py test apps.documents.tests.TestClassName.test_method_name  # Specific method
python manage.py test apps.documents               # Single app
python manage.py runserver                        # Start dev server
python manage.py runserver 0.0.0.0:8000          # Custom host/port
python manage.py makemigrations                   # Create migrations
python manage.py migrate                          # Apply migrations
python manage.py showmigrations                   # Show migrations
python manage.py shell                            # Django shell
python manage.py createsuperuser                  # Create admin
python manage.py collectstatic                    # Collect static files
docker-compose up --build                         # Build and run all
docker-compose up django                          # Run specific service
docker-compose up celery_worker                   # Run Celery worker
docker-compose exec django python manage.py <cmd> # Run in container
```

## Code Style Guidelines

### Import Order
1. Standard library (os, sys, io, uuid, logging, etc.)
2. Third-party (django, rest_framework, celery, pypdf, etc.)
3. Local imports (apps.xxx.models, apps.xxx.serializers, etc.)

```python
import io
import logging
from celery import shared_task
from django.db import models
from rest_framework import serializers
from apps.documents.models import Document
```

### Models
- Use `models.EmailField`, `models.TextField`, `models.IntegerField`
- Always use `on_delete=models.CASCADE` for ForeignKey
- Use `related_name` parameter in ForeignKey
- Include `__str__` method with f-string
- Use `auto_now_add=True` for created_at

```python
class Document(models.Model):
    url = models.TextField(max_length=250)
    name = models.TextField(max_length=250)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} - {self.type}"
```

### Serializers
- Inherit from `serializers.ModelSerializer` for models
- Use `serializers.Serializer` for non-model (file uploads)
- Use nested `Meta` class with `model` and `fields`
- Fields: `"__all__"` or explicit list

```python
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
```

### Views/ViewSets
- ViewSets use mixins (Retrieve, List, Create, Update, Destroy)
- Add docstrings with triple quotes
- Use `serializer_class` and `queryset` attributes
- Use `@extend_schema` for OpenAPI docs
- Return `Response` with `status` codes

```python
class DocumentViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for viewing, updating, and deleting documents."""
    serializer_class = serializers.DocumentSerializer
    queryset = Document.objects.all()
```

### Celery Tasks
- Use `@shared_task` decorator
- Init logger: `logger = logging.getLogger(__name__)`
- Use try-except blocks
- Return dict with `status` and `message`
- Use `logger.info/error/debug` levels
- Handle specific exceptions (e.g., `Document.DoesNotExist`)
- Re-raise exceptions for Celery retries

```python
import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def process_pdf(document_id):
    """Task to extract text from a PDF document."""
    logger.info("Starting PDF text extraction for document: %s", document_id)
    try:
        document = Document.objects.get(id=document_id)
        return {"status": "success", "message": "Processed successfully"}
    except Document.DoesNotExist:
        logger.error("Document not found: %s", document_id)
        return {"status": "error", "message": "Document not found"}
    except Exception as exc:
        logger.error("Error processing PDF %s: %s", document_id, exc)
        raise
```

### URL Patterns
- Use `path()` function
- Import viewsets/views directly
- Group URLs in app-specific urls.py

### Naming Conventions
- Classes: PascalCase (Document, User, DocumentUploadView)
- Functions/Methods: snake_case (process_pdf, get_document)
- Variables: snake_case (document_id, file_content)
- Constants: UPPER_SNAKE_CASE (INSTALLED_APPS, SECRET_KEY)
- Private methods: _underscore_prefix

### Error Handling
- Use try-except for failing operations
- Return Response with HTTP status codes
- `status.HTTP_400_BAD_REQUEST` for validation
- `status.HTTP_500_INTERNAL_SERVER_ERROR` for server errors
- Log errors with `logger.error`
- Catch specific exceptions

```python
from rest_framework import status
from rest_framework.response import Response

try:
    # operation
except Document.DoesNotExist:
    return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)
except Exception as e:
    logger.error("Error processing: %s", e)
    return Response({"error": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### Environment Configuration
- Use `environ.Env()` in `core/settings.py`
- Use `env()` with defaults
- Use `env.bool()`, `env.int()`, `env.list()` for typed
- Never commit `.env` files

```python
import environ

env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
```

### File Organization
- Models: `apps/<appname>/models.py`
- Serializers: `apps/<appname>/serializers.py`
- ViewSets: `apps/<appname>/viewsets.py`
- Views: `apps/<appname>/views.py`
- URLs: `apps/<appname>/urls.py`
- Tasks: `apps/<appname>/tasks.py`
- Utils: `apps/<appname>/utils.py`
- All apps in `apps/` directory
- Core config in `core/` directory

### Documentation
- Add docstrings to classes and complex functions
- Use `@extend_schema` for API endpoint docs
- Keep docstrings concise
