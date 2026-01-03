"""
共通スキーマ
"""

from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from enum import Enum


T = TypeVar("T")


class CamelCaseModel(BaseModel):
    """
    camelCase出力をサポートするベースモデル

    フロントエンド（JavaScript/TypeScript）との互換性のため、
    レスポンスをcamelCaseで返却する。
    入力はsnake_caseでもcamelCaseでも受け付ける。
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        serialize_by_alias=True,  # レスポンス時にcamelCaseを使用
    )


class ApiResponse(BaseModel, Generic[T]):
    """API成功レスポンス"""
    success: bool = True
    data: T
    message: Optional[str] = None


class ApiErrorDetail(BaseModel):
    """APIエラー詳細"""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ApiErrorResponse(BaseModel):
    """APIエラーレスポンス"""
    success: bool = False
    error: ApiErrorDetail


class PaginationParams(BaseModel):
    """ページネーションパラメータ"""
    page: int = Field(default=1, ge=1, description="ページ番号")
    page_size: int = Field(default=20, ge=1, le=100, description="1ページあたりの件数")
    sort_by: Optional[str] = Field(default=None, description="ソート対象カラム")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="ソート順")


class PaginatedResponse(BaseModel, Generic[T]):
    """ページネーション付きレスポンス"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        """ページネーションレスポンスを作成"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
