"""
LLM-optimized API documentation generator.

Parses OpenAPI schema from drf-spectacular and generates plain text documentation
optimized for consumption by Large Language Models.
"""

import json
from typing import Any


class LLMsTextGenerator:
    """Generates LLM-optimized API documentation from OpenAPI schema."""

    TYPE_EXAMPLES = {
        "string": "example_string",
        "integer": 1,
        "number": 1.5,
        "boolean": True,
        "array": [],
        "object": {},
    }

    FORMAT_EXAMPLES = {
        "date": "2024-01-15",
        "date-time": "2024-01-15T10:30:00Z",
        "email": "user@example.com",
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "uri": "https://example.com/resource",
        "binary": "<binary_data>",
    }

    FIELD_NAME_EXAMPLES = {
        "id": 1,
        "pk": 1,
        "page": 1,
        "page_start": 1,
        "page_end": 10,
        "num_questions": 5,
        "question": "What is the main concept discussed?",
        "answer": "The correct answer to the question",
        "title": "Example Title",
        "name": "Example Name",
        "description": "A detailed description of the resource",
        "content": "The main content of the resource",
        "document": 1,
        "document_id": 1,
        "exam": 1,
        "exam_id": 1,
        "user": 1,
        "user_id": 1,
        "score": 85.5,
        "total": 100,
        "count": 10,
        "next": "https://example.com/api/resource/?page=2",
        "previous": "https://example.com/api/resource/?page=1",
        "results": [],
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "is_correct": True,
        "is_active": True,
        "file": "https://example.com/files/document.pdf",
        "url": "https://example.com/api/resource/1/",
    }

    def __init__(self, schema: dict, base_url: str):
        """
        Initialize the generator.

        Args:
            schema: OpenAPI schema dictionary from drf-spectacular
            base_url: Base URL for the API
        """
        self.schema = schema
        self.base_url = base_url.rstrip("/")

    def generate(self) -> str:
        """Generate the complete LLM-optimized documentation."""
        sections = [
            self._generate_header(),
            self._generate_auth_section(),
            self._generate_endpoints_section(),
        ]
        return "\n".join(sections)

    def _generate_header(self) -> str:
        """Generate the header section with title, version, and base URL."""
        info = self.schema.get("info", {})
        title = info.get("title", "API Documentation")
        version = info.get("version", "1.0.0")
        description = info.get("description", "")

        lines = [
            f"# {title}",
            "",
            f"Version: {version}",
        ]

        if description:
            lines.extend(["", description])

        lines.extend([
            "",
            "## Base URL",
            "",
            f"    {self.base_url}/",
            "",
        ])

        return "\n".join(lines)

    def _generate_auth_section(self) -> str:
        """Generate the authentication section."""
        return """## Authentication

This API uses Clerk JWT authentication with Bearer tokens.

Include the following header in all authenticated requests:

    Authorization: Bearer <your_jwt_token>

---
"""

    def _generate_endpoints_section(self) -> str:
        """Generate documentation for all endpoints."""
        paths = self.schema.get("paths", {})
        if not paths:
            return "## Endpoints\n\nNo endpoints available.\n"

        lines = ["## Endpoints", ""]

        # Group endpoints by tag
        tagged_endpoints: dict[str, list[tuple[str, str, dict]]] = {}

        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ("get", "post", "put", "patch", "delete"):
                    tags = operation.get("tags", ["Other"])
                    tag = tags[0] if tags else "Other"

                    if tag not in tagged_endpoints:
                        tagged_endpoints[tag] = []
                    tagged_endpoints[tag].append((path, method.upper(), operation))

        # Generate documentation for each tag group
        for tag in sorted(tagged_endpoints.keys()):
            endpoints = tagged_endpoints[tag]
            lines.append(f"### {tag}")
            lines.append("")

            for path, method, operation in endpoints:
                lines.append(self._generate_endpoint_doc(path, method, operation))

        return "\n".join(lines)

    def _generate_endpoint_doc(self, path: str, method: str, operation: dict) -> str:
        """Generate documentation for a single endpoint."""
        lines = []

        # Title
        summary = operation.get("summary", operation.get("operationId", f"{method} {path}"))
        lines.append(f"#### {method} {path}")
        lines.append("")

        if summary:
            lines.append(summary)
            lines.append("")

        description = operation.get("description", "")
        if description and description != summary:
            lines.append(description)
            lines.append("")

        # Authentication
        security = operation.get("security", self.schema.get("security", []))
        if security:
            lines.append("**Authentication:** Required")
        else:
            lines.append("**Authentication:** Not required")
        lines.append("")

        # Parameters
        parameters = operation.get("parameters", [])
        if parameters:
            lines.append("**Parameters:**")
            for param in parameters:
                param_name = param.get("name", "")
                param_in = param.get("in", "query")
                param_required = "required" if param.get("required", False) else "optional"
                param_schema = param.get("schema", {})
                param_type = param_schema.get("type", "string")
                param_desc = param.get("description", "")

                param_line = f"- `{param_name}` ({param_type}, {param_in}, {param_required})"
                if param_desc:
                    param_line += f" - {param_desc}"
                lines.append(param_line)
            lines.append("")

        # Request Body
        request_body = operation.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})

            if schema:
                lines.append("**Request Body:**")
                lines.append("```json")
                example = self._generate_example_value(schema)
                lines.append(json.dumps(example, indent=4))
                lines.append("```")
                lines.append("")

        # Responses
        responses = operation.get("responses", {})
        for status_code, response in responses.items():
            response_desc = response.get("description", "")
            lines.append(f"**Response {status_code}:**{' ' + response_desc if response_desc else ''}")

            content = response.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})

            if schema:
                lines.append("```json")
                example = self._generate_example_value(schema)
                lines.append(json.dumps(example, indent=4))
                lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_example_value(self, schema: dict, field_name: str = "") -> Any:
        """
        Generate an example value from a schema definition.

        Args:
            schema: JSON Schema definition
            field_name: Name of the field (for context-aware examples)

        Returns:
            An example value matching the schema
        """
        # Handle $ref
        if "$ref" in schema:
            resolved = self._resolve_ref(schema["$ref"])
            return self._generate_example_value(resolved, field_name)

        # Check for explicit example
        if "example" in schema:
            return schema["example"]

        # Check for enum values
        if "enum" in schema:
            return schema["enum"][0] if schema["enum"] else None

        # Check field name for specific examples
        if field_name and field_name.lower() in self.FIELD_NAME_EXAMPLES:
            return self.FIELD_NAME_EXAMPLES[field_name.lower()]

        schema_type = schema.get("type", "string")
        schema_format = schema.get("format", "")

        # Check format-specific examples
        if schema_format in self.FORMAT_EXAMPLES:
            return self.FORMAT_EXAMPLES[schema_format]

        # Handle allOf, oneOf, anyOf
        if "allOf" in schema:
            merged = {}
            for sub_schema in schema["allOf"]:
                result = self._generate_example_value(sub_schema, field_name)
                if isinstance(result, dict):
                    merged.update(result)
            return merged if merged else self._generate_example_value(schema["allOf"][0], field_name)

        if "oneOf" in schema and schema["oneOf"]:
            return self._generate_example_value(schema["oneOf"][0], field_name)

        if "anyOf" in schema and schema["anyOf"]:
            return self._generate_example_value(schema["anyOf"][0], field_name)

        # Handle by type
        if schema_type == "object":
            properties = schema.get("properties", {})
            if not properties:
                return {}

            result = {}
            for prop_name, prop_schema in properties.items():
                result[prop_name] = self._generate_example_value(prop_schema, prop_name)
            return result

        if schema_type == "array":
            items = schema.get("items", {})
            item_example = self._generate_example_value(items, field_name)
            return [item_example]

        # Return type-based default
        return self.TYPE_EXAMPLES.get(schema_type, "example")

    def _resolve_ref(self, ref: str) -> dict:
        """
        Resolve a $ref reference to its schema definition.

        Args:
            ref: Reference string (e.g., "#/components/schemas/Exam")

        Returns:
            The resolved schema dictionary
        """
        if not ref.startswith("#/"):
            return {}

        parts = ref[2:].split("/")
        current = self.schema

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return {}

        return current if isinstance(current, dict) else {}
