# sql_injection_corrector.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re


@dataclass
class FieldRule:
    """
    Regla de validación/sanitización para un campo.
    - name: nombre del campo (ej. 'username', 'age')
    - field_type: 'string' | 'int' | 'email' (puedes agregar más)
    - max_length: longitud máxima permitida para cadenas
    - allowed_pattern: regex que define qué caracteres son válidos
    - required: si el campo es obligatorio
    """
    name: str
    field_type: str = "string"
    max_length: Optional[int] = None
    allowed_pattern: Optional[re.Pattern] = None
    required: bool = True


@dataclass
class CorrectionResult:
    """
    Resultado de la corrección de un campo.
    """
    field: str
    is_valid: bool
    original_value: Any
    sanitized_value: Any
    changes_made: bool
    messages: List[str]


class SQLInjectionCorrector:
    """
    Corrector / sanitizador básico para mitigar riesgos de SQL Injection.
    La lógica se basa en:
      - Validar tipo de dato (string, int, etc.).
      - Limitar longitud.
      - Eliminar secuencias típicas de SQL (--; /* */; etc.).
      - Restringir caracteres a un patrón permitido (whitelist).
    """

    def __init__(self, field_rules: List[FieldRule]):
        self.field_rules = {rule.name: rule for rule in field_rules}

        # Patrones genéricos de cosas que queremos evitar
        self._sql_meta_pattern = re.compile(r"(--|/\*|\*/|;)", re.IGNORECASE)
        self._sql_keywords_pattern = re.compile(
            r"\b(union|select|insert|update|delete|drop|truncate|shutdown|information_schema)\b",
            re.IGNORECASE
        )

        # Patrón sencillo para correos (opcional, solo ejemplo)
        self._email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, CorrectionResult]:
        """
        Recibe un diccionario de parámetros (ej. datos de un formulario)
        y devuelve un diccionario {campo: CorrectionResult}.
        """
        results: Dict[str, CorrectionResult] = {}

        for field_name, rule in self.field_rules.items():
            original_value = params.get(field_name, None)

            if original_value is None:
                if rule.required:
                    results[field_name] = CorrectionResult(
                        field=field_name,
                        is_valid=False,
                        original_value=None,
                        sanitized_value=None,
                        changes_made=False,
                        messages=["Campo requerido ausente."]
                    )
                else:
                    results[field_name] = CorrectionResult(
                        field=field_name,
                        is_valid=True,
                        original_value=None,
                        sanitized_value=None,
                        changes_made=False,
                        messages=["Campo opcional ausente."]
                    )
                continue

            # Enrutamos según el tipo
            if rule.field_type == "int":
                result = self._sanitize_int(field_name, original_value, rule)
            elif rule.field_type == "email":
                result = self._sanitize_email(field_name, original_value, rule)
            else:
                # Por defecto tratamos como string
                result = self._sanitize_string(field_name, original_value, rule)

            results[field_name] = result

        # También podemos reportar campos extra que no están en las reglas
        for extra_field in params.keys() - self.field_rules.keys():
            value = params[extra_field]
            results[extra_field] = CorrectionResult(
                field=extra_field,
                is_valid=True,
                original_value=value,
                sanitized_value=value,
                changes_made=False,
                messages=["Campo no definido en reglas; no se aplicó sanitización específica."]
            )

        return results

    def _sanitize_string(self, field: str, value: Any, rule: FieldRule) -> CorrectionResult:
        messages: List[str] = []
        changes_made = False

        # Convertimos a string
        s = str(value)
        original = s

        # Recortar espacios extremos
        s = s.strip()
        if s != original:
            changes_made = True
            messages.append("Se recortaron espacios al inicio/fin.")

        # Eliminar secuencias típicas de SQL (--, /*, */, ;)
        if self._sql_meta_pattern.search(s):
            s = self._sql_meta_pattern.sub("", s)
            changes_made = True
            messages.append("Se eliminaron secuencias típicas de SQL (--, /*, */, ;).")

        # Eliminar palabras clave SQL si aparecen completas (opcional, depende del uso).
        # En muchos casos no quieres permitir que el usuario escriba 'SELECT' o 'DROP'.
        if self._sql_keywords_pattern.search(s):
            s = self._sql_keywords_pattern.sub("", s)
            changes_made = True
            messages.append("Se eliminaron palabras clave SQL sospechosas (UNION, SELECT, DROP, etc.).")

        # Limitar longitud
        if rule.max_length is not None and len(s) > rule.max_length:
            s = s[:rule.max_length]
            changes_made = True
            messages.append(f"Se recortó a {rule.max_length} caracteres.")

        # Aplicar patrón de caracteres permitidos (whitelist)
        if rule.allowed_pattern is not None:
            # Mantener solo los caracteres que cumplen el patrón a nivel global
            # Aquí asumimos que allowed_pattern describe caracteres válidos (ej. r'[a-zA-Z0-9_@\.]+')
            allowed_chars_pattern = rule.allowed_pattern

            filtered = "".join(ch for ch in s if allowed_chars_pattern.match(ch))
            if filtered != s:
                s = filtered
                changes_made = True
                messages.append("Se eliminaron caracteres no permitidos por el patrón del campo.")

        is_valid = True

        # Si después de limpiar queda vacío y el campo es requerido
        if rule.required and s == "":
            is_valid = False
            messages.append("Tras la sanitización el valor quedó vacío en un campo requerido.")

        return CorrectionResult(
            field=field,
            is_valid=is_valid,
            original_value=original,
            sanitized_value=s,
            changes_made=changes_made,
            messages=messages
        )

    def _sanitize_int(self, field: str, value: Any, rule: FieldRule) -> CorrectionResult:
        messages: List[str] = []
        original = value
        changes_made = False

        try:
            # Intentamos castear directamente a int
            ivalue = int(str(value).strip())
        except ValueError:
            return CorrectionResult(
                field=field,
                is_valid=False,
                original_value=original,
                sanitized_value=None,
                changes_made=False,
                messages=["No se pudo convertir el valor a entero."]
            )
          
        # Por simplicidad, asumimos que cualquier int es válido.
        return CorrectionResult(
            field=field,
            is_valid=True,
            original_value=original,
            sanitized_value=ivalue,
            changes_made=changes_made,
            messages=messages
        )

    def _sanitize_email(self, field: str, value: Any, rule: FieldRule) -> CorrectionResult:
        messages: List[str] = []
        changes_made = False

        s = str(value).strip()
        original = s

        if rule.max_length is not None and len(s) > rule.max_length:
            s = s[:rule.max_length]
            changes_made = True
            messages.append(f"Se recortó el correo a {rule.max_length} caracteres.")

        # Validar formato básico de correo
        if not self._email_pattern.match(s):
            return CorrectionResult(
                field=field,
                is_valid=False,
                original_value=original,
                sanitized_value=None,
                changes_made=changes_made,
                messages=messages + ["Formato de correo inválido."]
            )

        # Opcional: aplicar patrón allowed_pattern 
        if rule.allowed_pattern is not None:
            allowed_chars_pattern = rule.allowed_pattern
            filtered = "".join(ch for ch in s if allowed_chars_pattern.match(ch))
            if filtered != s:
                s = filtered
                changes_made = True
                messages.append("Se eliminaron caracteres no permitidos en el correo.")

        return CorrectionResult(
            field=field,
            is_valid=True,
            original_value=original,
            sanitized_value=s,
            changes_made=changes_made,
            messages=messages
        )
