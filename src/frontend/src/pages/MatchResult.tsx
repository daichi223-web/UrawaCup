/**
 * 試合結果入力画面
 * スコア・得点者の入力
 */

import { useState, useEffect, useCallback } from 'react';
import { matchApi, type MatchScoreInput } from '@/features/matches';
import { MatchWithDetails, Goal } from '@shared/types';
import { Modal } from '@/components/ui/Modal';
import toast from 'react-hot-toast';
import { playerApi, type PlayerSuggestion } from '@/features/players';

// 得点入力用の型
interface GoalInput {
  id: string;
  teamId: number;
  teamType: 'home' | 'away';
  minute: number;
  half: 1 | 2;
  scorerName: string;
  playerId: number | null;
  isOwnGoal: boolean;
}

function MatchResult() {
  const [matches, setMatches] = useState<MatchWithDetails[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Filters
  const [dayFilter, setDayFilter] = useState('');
  const [venueFilter, setVenueFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<MatchWithDetails | null>(null);
  const [scoreForm, setScoreForm] = useState({
    homeScoreHalf1: 0,
    homeScoreHalf2: 0,
    awayScoreHalf1: 0,
    awayScoreHalf2: 0,
    homePK: 0,
    awayPK: 0,
    hasPenaltyShootout: false,
  });

  // 得点者入力
  const [goals, setGoals] = useState<GoalInput[]>([]);
  const [suggestions, setSuggestions] = useState<PlayerSuggestion[]>([]);
  const [activeGoalId, setActiveGoalId] = useState<string | null>(null);

  useEffect(() => {
    fetchMatches();
  }, [dayFilter, venueFilter, statusFilter]);

  const fetchMatches = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = {};
      if (statusFilter === 'pending') {
        params.status = 'scheduled';
      } else if (statusFilter === 'completed') {
        params.status = 'completed';
      }

      const data = await matchApi.getMatches(params);
      setMatches(data.matches);
    } catch (err: unknown) {
      console.error(err);
      setError('試合データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // 結果入力モーダルを開く
  const openScoreModal = (match: MatchWithDetails) => {
    setSelectedMatch(match);
    setScoreForm({
      homeScoreHalf1: match.homeScoreHalf1 ?? 0,
      homeScoreHalf2: match.homeScoreHalf2 ?? 0,
      awayScoreHalf1: match.awayScoreHalf1 ?? 0,
      awayScoreHalf2: match.awayScoreHalf2 ?? 0,
      homePK: match.homePK ?? 0,
      awayPK: match.awayPK ?? 0,
      hasPenaltyShootout: match.hasPenaltyShootout ?? false,
    });
    // 既存の得点をGoalInput形式に変換
    const existingGoals: GoalInput[] = (match.goals || []).map((g: Goal, idx: number) => ({
      id: `existing-${idx}`,
      teamId: g.teamId,
      teamType: g.teamId === match.homeTeamId ? 'home' : 'away',
      minute: g.minute,
      half: g.half,
      scorerName: (g as any).scorerName || g.playerName || "",
      playerId: g.playerId ?? null,
      isOwnGoal: g.isOwnGoal ?? false,
    }));
    setGoals(existingGoals);
    setSuggestions([]);
    setActiveGoalId(null);
    setShowModal(true);
  };

  // 得点を追加
  const addGoal = () => {
    const newGoal: GoalInput = {
      id: `new-${Date.now()}`,
      teamId: selectedMatch?.homeTeamId || 0,
      teamType: 'home',
      minute: 1,
      half: 1,
      scorerName: '',
      playerId: null,
      isOwnGoal: false,
    };
    setGoals(prev => [...prev, newGoal]);
  };

  // 得点を削除
  const removeGoal = (id: string) => {
    setGoals(prev => prev.filter(g => g.id !== id));
  };

  // 得点を更新
  const updateGoal = (id: string, updates: Partial<GoalInput>) => {
    setGoals(prev => prev.map(g => {
      if (g.id !== id) return g;
      const updated = { ...g, ...updates };
      if (updates.teamType && selectedMatch) {
        updated.teamId = updates.teamType === 'home' ? selectedMatch.homeTeamId : selectedMatch.awayTeamId;
      }
      return updated;
    }));
  };

  // 選手サジェスト検索
  const searchPlayers = useCallback(async (goalId: string, query: string) => {
    if (!selectedMatch || query.length < 1) {
      setSuggestions([]);
      return;
    }
    const goal = goals.find(g => g.id === goalId);
    if (!goal) return;
    try {
      const results = await playerApi.suggest(goal.teamId, query);
      setSuggestions(results);
      setActiveGoalId(goalId);
    } catch (err) {
      console.error('Failed to fetch suggestions:', err);
      setSuggestions([]);
    }
  }, [selectedMatch, goals]);

  // サジェストを選択
  const selectSuggestion = (goalId: string, suggestion: PlayerSuggestion) => {
    updateGoal(goalId, { scorerName: suggestion.name, playerId: suggestion.id });
    setSuggestions([]);
    setActiveGoalId(null);
  };

  // スコアを保存
  const handleSaveScore = async () => {
    if (!selectedMatch) return;

    setSaving(true);
    try {
      const scoreData: MatchScoreInput = {
        homeScoreHalf1: scoreForm.homeScoreHalf1,
        homeScoreHalf2: scoreForm.homeScoreHalf2,
        awayScoreHalf1: scoreForm.awayScoreHalf1,
        awayScoreHalf2: scoreForm.awayScoreHalf2,
        hasPenaltyShootout: scoreForm.hasPenaltyShootout,
        goals: goals.map(g => ({
          teamId: g.teamId,
          playerId: g.playerId,
          scorerName: (g as any).scorerName || (g as any).playerName || "",
          minute: g.minute,
          half: g.half,
          isOwnGoal: g.isOwnGoal,
        })),
      };

      if (scoreForm.hasPenaltyShootout) {
        scoreData.homePk = scoreForm.homePK;
        scoreData.awayPk = scoreForm.awayPK;
      }

      await matchApi.updateScore(selectedMatch.id, scoreData);

      // 試合リストを更新
      const updatedMatches = matches.map(m => {
        if (m.id === selectedMatch.id) {
          return {
            ...m,
            homeScoreHalf1: scoreForm.homeScoreHalf1,
            homeScoreHalf2: scoreForm.homeScoreHalf2,
            awayScoreHalf1: scoreForm.awayScoreHalf1,
            awayScoreHalf2: scoreForm.awayScoreHalf2,
            homeScoreTotal: scoreForm.homeScoreHalf1 + scoreForm.homeScoreHalf2,
            awayScoreTotal: scoreForm.awayScoreHalf1 + scoreForm.awayScoreHalf2,
            homePK: scoreForm.homePK,
            awayPK: scoreForm.awayPK,
            hasPenaltyShootout: scoreForm.hasPenaltyShootout,
            status: 'completed' as const,
          };
        }
        return m;
      });
      setMatches(updatedMatches);

      setShowModal(false);
      toast.success('試合結果を保存しました');
    } catch (err: unknown) {
      console.error(err);
      const message = err instanceof Error ? err.message : '保存に失敗しました';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  // 合計得点を計算
  const homeTotal = scoreForm.homeScoreHalf1 + scoreForm.homeScoreHalf2;
  const awayTotal = scoreForm.awayScoreHalf1 + scoreForm.awayScoreHalf2;

  return (
    <div className="space-y-6">
      {/* ページヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">試合結果入力</h1>
        <p className="text-gray-600 mt-1">
          試合のスコアと得点者を入力します
        </p>
      </div>

      {/* フィルター */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label className="form-label">日付</label>
              <select
                className="form-input"
                value={dayFilter}
                onChange={(e) => setDayFilter(e.target.value)}
              >
                <option value="">日付を選択</option>
                <option value="day1">Day1 (予選)</option>
                <option value="day2">Day2 (予選)</option>
                <option value="day3">Day3 (決勝T)</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="form-label">会場</label>
              <select
                className="form-input"
                value={venueFilter}
                onChange={(e) => setVenueFilter(e.target.value)}
              >
                <option value="">全会場</option>
                <option value="urawa-minami">浦和南高G</option>
                <option value="ichiritu">市立浦和高G</option>
                <option value="uragaku">浦和学院G</option>
                <option value="bunan">武南高G</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="form-label">状態</label>
              <select
                className="form-input"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">すべて</option>
                <option value="pending">未入力</option>
                <option value="completed">入力済み</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 試合一覧 */}
      <div className="space-y-4">
        {loading ? (
          <p className="text-center py-8 text-gray-500">読み込み中...</p>
        ) : error ? (
          <p className="text-center py-8 text-red-500">{error}</p>
        ) : matches.length === 0 ? (
          <p className="text-center py-8 text-gray-500">
            試合データがありません。日程を生成してください。
          </p>
        ) : (
          <div className="grid gap-4">
            {matches.map((match) => (
              <div key={match.id} className="card hover:shadow-md transition-shadow">
                <div className="card-body p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-500">
                      {match.matchOrder}試合目 {match.matchTime} @ {match.venue?.name}
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${match.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {match.status === 'completed' ? '完了' : '未入力'}
                    </div>
                  </div>

                  <div className="flex justify-between items-center mt-3">
                    <div className="flex-1 text-right font-bold text-lg">
                      {match.homeTeam?.name}
                    </div>
                    <div className="mx-4 text-2xl font-bold bg-gray-100 px-4 py-1 rounded">
                      {match.homeScoreTotal ?? '-'} - {match.awayScoreTotal ?? '-'}
                    </div>
                    <div className="flex-1 text-left font-bold text-lg">
                      {match.awayTeam?.name}
                    </div>
                  </div>

                  <div className="mt-4 text-right">
                    <button
                      className="btn-primary text-sm px-4 py-2"
                      onClick={() => openScoreModal(match)}
                    >
                      {match.status === 'completed' ? '修正' : '結果入力'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 結果入力モーダル */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="試合結果入力"
      >
        {selectedMatch && (
          <div className="space-y-6">
            {/* 試合情報 */}
            <div className="text-center text-sm text-gray-500">
              {selectedMatch.matchDate} {selectedMatch.matchTime} @ {selectedMatch.venue?.name}
            </div>

            {/* チーム名とスコア表示 */}
            <div className="flex items-center justify-center gap-4">
              <div className="text-center flex-1">
                <div className="font-bold text-lg">{selectedMatch.homeTeam?.name}</div>
                <div className="text-3xl font-bold text-primary-600 mt-2">
                  {homeTotal}
                </div>
              </div>
              <div className="text-2xl text-gray-400">vs</div>
              <div className="text-center flex-1">
                <div className="font-bold text-lg">{selectedMatch.awayTeam?.name}</div>
                <div className="text-3xl font-bold text-primary-600 mt-2">
                  {awayTotal}
                </div>
              </div>
            </div>

            {/* 前半スコア */}
            <div className="border rounded-lg p-4">
              <h4 className="font-medium text-gray-700 mb-3">前半</h4>
              <div className="flex items-center justify-center gap-4">
                <div className="flex-1">
                  <input
                    type="number"
                    min="0"
                    max="99"
                    className="form-input text-center text-xl font-bold w-full"
                    value={scoreForm.homeScoreHalf1}
                    onChange={(e) => setScoreForm(prev => ({ ...prev, homeScoreHalf1: parseInt(e.target.value) || 0 }))}
                  />
                </div>
                <span className="text-gray-400">-</span>
                <div className="flex-1">
                  <input
                    type="number"
                    min="0"
                    max="99"
                    className="form-input text-center text-xl font-bold w-full"
                    value={scoreForm.awayScoreHalf1}
                    onChange={(e) => setScoreForm(prev => ({ ...prev, awayScoreHalf1: parseInt(e.target.value) || 0 }))}
                  />
                </div>
              </div>
            </div>

            {/* 後半スコア */}
            <div className="border rounded-lg p-4">
              <h4 className="font-medium text-gray-700 mb-3">後半</h4>
              <div className="flex items-center justify-center gap-4">
                <div className="flex-1">
                  <input
                    type="number"
                    min="0"
                    max="99"
                    className="form-input text-center text-xl font-bold w-full"
                    value={scoreForm.homeScoreHalf2}
                    onChange={(e) => setScoreForm(prev => ({ ...prev, homeScoreHalf2: parseInt(e.target.value) || 0 }))}
                  />
                </div>
                <span className="text-gray-400">-</span>
                <div className="flex-1">
                  <input
                    type="number"
                    min="0"
                    max="99"
                    className="form-input text-center text-xl font-bold w-full"
                    value={scoreForm.awayScoreHalf2}
                    onChange={(e) => setScoreForm(prev => ({ ...prev, awayScoreHalf2: parseInt(e.target.value) || 0 }))}
                  />
                </div>
              </div>
            </div>

            {/* PK戦 */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <input
                  type="checkbox"
                  id="hasPK"
                  checked={scoreForm.hasPenaltyShootout}
                  onChange={(e) => setScoreForm(prev => ({ ...prev, hasPenaltyShootout: e.target.checked }))}
                  className="h-4 w-4 rounded border-gray-300 text-primary-600"
                />
                <label htmlFor="hasPK" className="font-medium text-gray-700">
                  PK戦
                </label>
              </div>
              {scoreForm.hasPenaltyShootout && (
                <div className="flex items-center justify-center gap-4">
                  <div className="flex-1">
                    <input
                      type="number"
                      min="0"
                      max="99"
                      className="form-input text-center text-xl font-bold w-full"
                      value={scoreForm.homePK}
                      onChange={(e) => setScoreForm(prev => ({ ...prev, homePK: parseInt(e.target.value) || 0 }))}
                    />
                  </div>
                  <span className="text-gray-400">-</span>
                  <div className="flex-1">
                    <input
                      type="number"
                      min="0"
                      max="99"
                      className="form-input text-center text-xl font-bold w-full"
                      value={scoreForm.awayPK}
                      onChange={(e) => setScoreForm(prev => ({ ...prev, awayPK: parseInt(e.target.value) || 0 }))}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* 得点者入力 */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-700">得点者</h4>
                <button type="button" className="text-sm text-primary-600 hover:text-primary-800" onClick={addGoal}>+ 追加</button>
              </div>
              {goals.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-2">得点者を追加してください</p>
              ) : (
                <div className="space-y-3">
                  {goals.map((goal) => (
                    <div key={goal.id} className="flex items-start gap-2 p-2 bg-gray-50 rounded">
                      <div className="w-16">
                        <input type="number" min="1" max="99" className="form-input text-center text-sm w-full" value={goal.minute}
                          onChange={(e) => updateGoal(goal.id, { minute: parseInt(e.target.value) || 1 })} placeholder="分" />
                      </div>
                      <select className="form-input text-sm w-20" value={goal.half}
                        onChange={(e) => updateGoal(goal.id, { half: parseInt(e.target.value) as 1 | 2 })}>
                        <option value={1}>前半</option>
                        <option value={2}>後半</option>
                      </select>
                      <select className="form-input text-sm flex-1" value={goal.teamType}
                        onChange={(e) => updateGoal(goal.id, { teamType: e.target.value as 'home' | 'away' })}>
                        <option value="home">{selectedMatch?.homeTeam?.name}</option>
                        <option value="away">{selectedMatch?.awayTeam?.name}</option>
                      </select>
                      <div className="flex-1 relative">
                        <input type="text" className="form-input text-sm w-full" value={goal.scorerName}
                          onChange={(e) => { updateGoal(goal.id, { scorerName: e.target.value, playerId: null }); searchPlayers(goal.id, e.target.value); }}
                          placeholder="得点者名" />
                        {activeGoalId === goal.id && suggestions.length > 0 && (
                          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                            {suggestions.map((s) => (
                              <button key={s.id} type="button" className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
                                onClick={() => selectSuggestion(goal.id, s)}>#{s.number} {s.name}</button>
                            ))}
                          </div>
                        )}
                      </div>
                      <label className="flex items-center gap-1 text-sm text-gray-600 whitespace-nowrap">
                        <input type="checkbox" checked={goal.isOwnGoal}
                          onChange={(e) => updateGoal(goal.id, { isOwnGoal: e.target.checked })}
                          className="h-4 w-4 rounded border-gray-300 text-primary-600" />OG
                      </label>
                      <button type="button" className="text-red-500 hover:text-red-700 p-1" onClick={() => removeGoal(goal.id)}>×</button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ボタン */}
            <div className="flex justify-end gap-3 pt-4">
              <button
                className="btn-secondary"
                onClick={() => setShowModal(false)}
              >
                キャンセル
              </button>
              <button
                className="btn-primary"
                onClick={handleSaveScore}
                disabled={saving}
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default MatchResult
