"""Excepciones de dominio propias de Óleo & Lienzo."""


class DomainError(Exception):
    """Excepción base de dominio. status_code y detail para la respuesta HTTP."""

    status_code: int = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class UnauthorizedError(DomainError):
    status_code = 401


class ForbiddenError(DomainError):
    status_code = 403


class BusinessRuleError(DomainError):
    status_code = 422
