"""
Player（選手）モデル

仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

import re
import unicodedata
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


def normalize_name(name: str, kana: str | None = None) -> str:
    """
    検索用に名前を正規化
    - 全角カタカナに統一
    - 空白除去
    - ひらがな→カタカナ変換
    """
    target = kana if kana else name

    # NFKC正規化（全角カタカナに変換）
    normalized = unicodedata.normalize('NFKC', target)

    # ひらがな→カタカナ変換
    result = []
    for c in normalized:
        if 'ぁ' <= c <= 'ん':
            result.append(chr(ord(c) + 96))
        else:
            result.append(c)
    normalized = ''.join(result)

    # 空白除去
    normalized = re.sub(r'\s+', '', normalized)

    return normalized


class Player(Base, TimestampMixin):
    """
    選手情報テーブル

    1チームあたり26〜50名程度の登録に対応。
    得点者入力時のサジェスト機能で使用。
    """

    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)

    # 基本情報
    number = Column(Integer, nullable=True, comment="背番号（NULL許容：未定の場合）")
    name = Column(String(100), nullable=False, comment="氏名")
    name_kana = Column(String(100), nullable=True, comment="フリガナ")
    name_normalized = Column(String(100), nullable=True, comment="検索用（カタカナ正規化）")

    # 選手属性
    grade = Column(Integer, nullable=True, comment="学年（1-3）")
    position = Column(String(20), nullable=True, comment="ポジション（GK/DF/MF/FW）")
    height = Column(Integer, nullable=True, comment="身長(cm)")
    previous_team = Column(String(100), nullable=True, comment="前所属チーム（中学校/クラブ）")

    # フラグ
    is_captain = Column(Boolean, nullable=False, default=False, comment="キャプテン")
    is_active = Column(Boolean, nullable=False, default=True, comment="有効フラグ（論理削除用）")

    # 備考
    notes = Column(String(500), nullable=True, comment="備考")

    # リレーション
    team = relationship("Team", back_populates="players")
    goals = relationship("Goal", back_populates="player")

    # インデックス
    __table_args__ = (
        Index('idx_players_team', 'team_id'),
        Index('idx_players_name_normalized', 'name_normalized'),
        Index('idx_players_active', 'team_id', 'is_active'),
    )

    def __repr__(self):
        number_str = str(self.number) if self.number else '-'
        return f"<Player(id={self.id}, number={number_str}, name='{self.name}')>"

    def update_normalized_name(self):
        """検索用正規化名を更新"""
        self.name_normalized = normalize_name(self.name, self.name_kana)

    @property
    def display_text(self) -> str:
        """得点者入力用の表示テキスト"""
        number_str = str(self.number) if self.number else '-'
        return f"{number_str} {self.name}"

    @property
    def full_display_text(self) -> str:
        """詳細表示用のテキスト（背番号、名前、学年、ポジション）"""
        number_str = f"#{self.number}" if self.number else ""
        grade_str = f"{self.grade}年" if self.grade else ""
        pos_str = self.position if self.position else ""
        return f"{self.name} {number_str} {grade_str} {pos_str}".strip()
