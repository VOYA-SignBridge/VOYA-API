from typing import TypeVar, Generic, Sequence
from fastapi import Query
from fastapi_pagination import Page as BasePage, Params
from fastapi_pagination.bases import AbstractPage, AbstractParams
from pydantic import Field

T = TypeVar("T") 
class MyCustomParams(Params):
    page: int = Query(1, ge=1, alias="p")
    size: int = Query(20, ge=1, le=100, alias="s")
class PageResponse(AbstractPage[T], Generic[T]):
    data: Sequence[T]        
    total_records: int        
    current_page: int        
    page_size: int           

    __params_type__ = MyCustomParams 

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        params: AbstractParams,
    ):
        return cls(
            data=items,
            total_records=total,
            current_page=params.page,
            page_size=params.size,
        )