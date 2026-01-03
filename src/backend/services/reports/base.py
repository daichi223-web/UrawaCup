"""
報告書生成基底クラス

全ての報告書ジェネレータの共通機能を提供
"""

import io
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Any

from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class BaseReportGenerator(ABC):
    """報告書生成基底クラス"""

    # PDF設定（TournaMate_Report_Formats.md Section 2.3）
    PAGE_SIZE = A4
    MARGIN_TOP = 20 * mm
    MARGIN_BOTTOM = 20 * mm
    MARGIN_LEFT = 20 * mm
    MARGIN_RIGHT = 20 * mm

    FONT_SIZE_TITLE = 14
    FONT_SIZE_BODY = 10
    FONT_SIZE_TABLE = 9

    def __init__(self, db: Session):
        self.db = db
        self._font_name = self._register_font()

    def _register_font(self) -> str:
        """
        日本語フォントを登録

        優先順位:
        1. Windows: MS ゴシック
        2. Mac: ヒラギノ角ゴシック
        3. フォールバック: Helvetica
        """
        font_paths = [
            # Windows
            ("Gothic", "C:/Windows/Fonts/msgothic.ttc"),
            ("Gothic", "C:/Windows/Fonts/YuGothM.ttc"),
            # Mac
            ("Gothic", "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),
            ("Gothic", "/Library/Fonts/Arial Unicode.ttf"),
            # Linux
            ("Gothic", "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf"),
            ("Gothic", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        ]

        for font_name, font_path in font_paths:
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
            except:
                continue

        # フォールバック
        return "Helvetica"

    @abstractmethod
    def generate(self, output_path: Optional[str] = None) -> io.BytesIO:
        """
        報告書を生成

        Args:
            output_path: 出力パス（省略時はBytesIOを返す）

        Returns:
            生成されたPDFのBytesIO
        """
        pass

    def _create_canvas(self, buffer: io.BytesIO) -> canvas.Canvas:
        """PDFキャンバスを作成"""
        return canvas.Canvas(buffer, pagesize=self.PAGE_SIZE)

    def _draw_header(
        self,
        c: canvas.Canvas,
        title: str,
        subtitle: Optional[str] = None
    ) -> float:
        """
        ヘッダーを描画

        Returns:
            ヘッダー下のY座標
        """
        width, height = self.PAGE_SIZE
        y = height - self.MARGIN_TOP

        c.setFont(self._font_name, self.FONT_SIZE_TITLE)
        c.drawString(self.MARGIN_LEFT, y, title)
        y -= 8 * mm

        if subtitle:
            c.setFont(self._font_name, self.FONT_SIZE_BODY)
            c.drawString(self.MARGIN_LEFT, y, subtitle)
            y -= 6 * mm

        return y

    def _draw_footer(self, c: canvas.Canvas, text: str = "浦和カップ運営事務局"):
        """フッターを描画"""
        c.setFont(self._font_name, 8)
        c.drawString(self.MARGIN_LEFT, self.MARGIN_BOTTOM - 5 * mm, text)

    def _new_page_if_needed(
        self,
        c: canvas.Canvas,
        current_y: float,
        required_height: float
    ) -> float:
        """
        必要に応じて改ページ

        Args:
            c: キャンバス
            current_y: 現在のY座標
            required_height: 必要な高さ

        Returns:
            新しいY座標
        """
        if current_y - required_height < self.MARGIN_BOTTOM:
            c.showPage()
            _, height = self.PAGE_SIZE
            return height - self.MARGIN_TOP
        return current_y

    def _calculate_day_number(self, tournament_start: date, target_date: date) -> int:
        """
        大会日数を計算

        Args:
            tournament_start: 大会開始日
            target_date: 対象日

        Returns:
            第N日の数字
        """
        return (target_date - tournament_start).days + 1
