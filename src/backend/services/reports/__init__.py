"""
Reports サブモジュール - 報告書生成

TournaMate_Report_Formats.md に基づく報告書生成機能を提供。

報告書の種類:
- DailyReportGenerator: 日次試合結果報告書
- FinalDayScheduleGenerator: 最終日組み合わせ表
- FinalResultReportGenerator: 最終結果報告書
- TrainingMatchReportGenerator: 研修試合一覧表
"""

from .base import BaseReportGenerator
from .daily_report import DailyReportGenerator
from .final_day_schedule import FinalDayScheduleGenerator
from .final_result_report import FinalResultReportGenerator
from .types import (
    DailyReportData,
    MatchResultData,
    GoalData,
    SenderInfo,
    FinalDayScheduleData,
    FinalDayVenueSchedule,
    FinalDayMatch,
    FinalReportData,
    FinalRanking,
    OutstandingPlayer,
    KnockoutMatch,
)

__all__ = [
    "BaseReportGenerator",
    "DailyReportGenerator",
    "FinalDayScheduleGenerator",
    "FinalResultReportGenerator",
    "DailyReportData",
    "MatchResultData",
    "GoalData",
    "SenderInfo",
    "FinalDayScheduleData",
    "FinalDayVenueSchedule",
    "FinalDayMatch",
    "FinalReportData",
    "FinalRanking",
    "OutstandingPlayer",
    "KnockoutMatch",
]
