"""
UrawaCup 要件チェックSDK
Claude Agent SDKを使用して要件の実装状況をチェックする
"""

from .requirements_data import (
    Requirement,
    Phase,
    Priority,
    ImplementationStatus,
    ALL_REQUIREMENTS,
    MINI_REQUIREMENTS,
    MIDDLE_REQUIREMENTS,
    MAX_REQUIREMENTS,
    ENTITY_REQUIREMENTS,
    get_requirements_by_phase,
    get_requirements_by_priority,
    get_requirements_by_category,
    get_all_categories,
)

from .code_checker import (
    CodeChecker,
    CheckResult,
    CheckSummary,
    format_check_result,
    format_summary,
)

__version__ = "1.0.0"
__all__ = [
    "Requirement",
    "Phase",
    "Priority",
    "ImplementationStatus",
    "ALL_REQUIREMENTS",
    "MINI_REQUIREMENTS",
    "MIDDLE_REQUIREMENTS",
    "MAX_REQUIREMENTS",
    "ENTITY_REQUIREMENTS",
    "get_requirements_by_phase",
    "get_requirements_by_priority",
    "get_requirements_by_category",
    "get_all_categories",
    "CodeChecker",
    "CheckResult",
    "CheckSummary",
    "format_check_result",
    "format_summary",
]
