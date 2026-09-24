from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    page: int
    page_size: int


def pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)
