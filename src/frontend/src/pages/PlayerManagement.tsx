// src/frontend/src/pages/PlayerManagement.tsx
// 選手管理ページ
import { useState, useRef } from 'react';
import { useTeams } from '@/features/teams/hooks';
import {
  usePlayersByTeam,
  useCreatePlayer,
  useUpdatePlayer,
  useDeletePlayer,
  useImportExcel,
} from '@/features/players/hooks';
import type { Player, CreatePlayerInput, UpdatePlayerInput } from '@/features/players/types';
import toast from 'react-hot-toast';

const POSITIONS = ['GK', 'DF', 'MF', 'FW'] as const;
const GRADES = [1, 2, 3, 4, 5, 6] as const;

export default function PlayerManagement() {
  // TODO: 将来的にトーナメント選択機能を実装
  const tournamentId = 1;
  const { data: teams = [] } = useTeams(tournamentId);

  // 選択中のチーム
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const { data: players = [], isLoading: loadingPlayers } = usePlayersByTeam(selectedTeamId || 0);

  // モーダル状態
  const [showModal, setShowModal] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletingPlayer, setDeletingPlayer] = useState<Player | null>(null);

  // フォーム
  const [form, setForm] = useState<CreatePlayerInput>({
    teamId: 0,
    number: null,
    name: '',
    nameKana: '',
    grade: undefined,
    position: undefined,
    height: undefined,
    previousTeam: '',
    isCaptain: false,
    notes: '',
  });

  // Excelインポート
  const excelInputRef = useRef<HTMLInputElement>(null);
  const importExcelMutation = useImportExcel();

  // Mutations
  const createMutation = useCreatePlayer();
  const updateMutation = useUpdatePlayer();
  const deleteMutation = useDeletePlayer();

  // 新規追加モーダルを開く
  const openAddModal = () => {
    if (!selectedTeamId) {
      toast.error('チームを選択してください');
      return;
    }
    setEditingPlayer(null);
    setForm({
      teamId: selectedTeamId,
      number: null,
      name: '',
      nameKana: '',
      grade: undefined,
      position: undefined,
      height: undefined,
      previousTeam: '',
      isCaptain: false,
      notes: '',
    });
    setShowModal(true);
  };

  // 編集モーダルを開く
  const openEditModal = (player: Player) => {
    setEditingPlayer(player);
    setForm({
      teamId: player.teamId,
      number: player.number,
      name: player.name,
      nameKana: player.nameKana || '',
      grade: player.grade || undefined,
      position: player.position || undefined,
      height: player.height || undefined,
      previousTeam: player.previousTeam || '',
      isCaptain: player.isCaptain,
      notes: player.notes || '',
    });
    setShowModal(true);
  };

  // 保存
  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error('選手名を入力してください');
      return;
    }

    try {
      if (editingPlayer) {
        const updateData: UpdatePlayerInput = {
          number: form.number,
          name: form.name,
          nameKana: form.nameKana,
          grade: form.grade,
          position: form.position,
          height: form.height,
          previousTeam: form.previousTeam,
          isCaptain: form.isCaptain,
          notes: form.notes,
        };
        await updateMutation.mutateAsync({ id: editingPlayer.id, data: updateData });
        toast.success('選手を更新しました');
      } else {
        await createMutation.mutateAsync(form);
        toast.success('選手を追加しました');
      }
      setShowModal(false);
    } catch (error) {
      toast.error('保存に失敗しました');
    }
  };

  // 削除確認
  const confirmDelete = (player: Player) => {
    setDeletingPlayer(player);
    setShowDeleteConfirm(true);
  };

  // 削除実行
  const handleDelete = async () => {
    if (!deletingPlayer) return;
    try {
      await deleteMutation.mutateAsync(deletingPlayer.id);
      toast.success('選手を削除しました');
      setShowDeleteConfirm(false);
      setDeletingPlayer(null);
    } catch (error) {
      toast.error('削除に失敗しました');
    }
  };

  // Excelインポート
  const handleExcelImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedTeamId) return;

    try {
      const result = await importExcelMutation.mutateAsync({
        teamId: selectedTeamId,
        file,
        options: { replaceExisting: false },
      });
      toast.success(`${result.imported}名をインポート、${result.updated}名を更新しました`);
    } catch (error) {
      toast.error('インポートに失敗しました');
    }

    // ファイル入力をリセット
    if (excelInputRef.current) {
      excelInputRef.current.value = '';
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">選手管理</h1>
        <div className="flex items-center gap-3">
          {/* チーム選択 */}
          <select
            className="form-input w-64"
            value={selectedTeamId || ''}
            onChange={(e) => setSelectedTeamId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">チームを選択...</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>

          {/* Excelインポート */}
          <input
            type="file"
            ref={excelInputRef}
            accept=".xlsx,.xls"
            className="hidden"
            onChange={handleExcelImport}
          />
          <button
            className="btn-secondary"
            onClick={() => excelInputRef.current?.click()}
            disabled={!selectedTeamId || importExcelMutation.isPending}
          >
            Excelインポート
          </button>

          {/* 選手追加 */}
          <button
            className="btn-primary"
            onClick={openAddModal}
            disabled={!selectedTeamId}
          >
            + 選手追加
          </button>
        </div>
      </div>

      {/* 選手一覧 */}
      {!selectedTeamId ? (
        <div className="text-center py-12 text-gray-500">
          チームを選択してください
        </div>
      ) : loadingPlayers ? (
        <div className="text-center py-12 text-gray-500">読み込み中...</div>
      ) : players.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          選手が登録されていません
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">背番号</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">選手名</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">フリガナ</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">学年</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">ポジション</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">身長</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">前所属</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">C</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {players.map((player) => (
                <tr key={player.id} className={!player.isActive ? 'bg-gray-50 opacity-60' : ''}>
                  <td className="px-4 py-3 text-sm">{player.number ?? '-'}</td>
                  <td className="px-4 py-3 text-sm font-medium">{player.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{player.nameKana || '-'}</td>
                  <td className="px-4 py-3 text-sm">{player.grade ? `${player.grade}年` : '-'}</td>
                  <td className="px-4 py-3 text-sm">{player.position || '-'}</td>
                  <td className="px-4 py-3 text-sm">{player.height ? `${player.height}cm` : '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{player.previousTeam || '-'}</td>
                  <td className="px-4 py-3 text-center">
                    {player.isCaptain && <span className="text-yellow-500">★</span>}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      className="text-primary-600 hover:text-primary-800 mr-3"
                      onClick={() => openEditModal(player)}
                    >
                      編集
                    </button>
                    <button
                      className="text-red-600 hover:text-red-800"
                      onClick={() => confirmDelete(player)}
                    >
                      削除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 追加/編集モーダル */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
            <h2 className="text-xl font-bold mb-4">
              {editingPlayer ? '選手編集' : '選手追加'}
            </h2>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">背番号</label>
                  <input
                    type="number"
                    min="1"
                    max="99"
                    className="form-input w-full"
                    value={form.number ?? ''}
                    onChange={(e) => setForm({ ...form, number: e.target.value ? Number(e.target.value) : null })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    選手名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    className="form-input w-full"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">フリガナ</label>
                <input
                  type="text"
                  className="form-input w-full"
                  value={form.nameKana}
                  onChange={(e) => setForm({ ...form, nameKana: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">学年</label>
                  <select
                    className="form-input w-full"
                    value={form.grade ?? ''}
                    onChange={(e) => setForm({ ...form, grade: e.target.value ? Number(e.target.value) : undefined })}
                  >
                    <option value="">-</option>
                    {GRADES.map((g) => (
                      <option key={g} value={g}>{g}年</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ポジション</label>
                  <select
                    className="form-input w-full"
                    value={form.position ?? ''}
                    onChange={(e) => setForm({ ...form, position: e.target.value as typeof POSITIONS[number] || undefined })}
                  >
                    <option value="">-</option>
                    {POSITIONS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">身長(cm)</label>
                  <input
                    type="number"
                    min="100"
                    max="220"
                    className="form-input w-full"
                    value={form.height ?? ''}
                    onChange={(e) => setForm({ ...form, height: e.target.value ? Number(e.target.value) : undefined })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">前所属チーム</label>
                <input
                  type="text"
                  className="form-input w-full"
                  value={form.previousTeam}
                  onChange={(e) => setForm({ ...form, previousTeam: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">備考</label>
                <textarea
                  className="form-input w-full"
                  rows={2}
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isCaptain"
                  className="h-4 w-4 rounded border-gray-300 text-primary-600"
                  checked={form.isCaptain}
                  onChange={(e) => setForm({ ...form, isCaptain: e.target.checked })}
                />
                <label htmlFor="isCaptain" className="ml-2 text-sm text-gray-700">
                  キャプテン
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                className="btn-secondary"
                onClick={() => setShowModal(false)}
              >
                キャンセル
              </button>
              <button
                className="btn-primary"
                onClick={handleSave}
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {(createMutation.isPending || updateMutation.isPending) ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 削除確認モーダル */}
      {showDeleteConfirm && deletingPlayer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-bold mb-4">選手の削除</h2>
            <p className="text-gray-600 mb-6">
              「{deletingPlayer.name}」を削除しますか？<br />
              この操作は取り消せません。
            </p>
            <div className="flex justify-end gap-3">
              <button
                className="btn-secondary"
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeletingPlayer(null);
                }}
              >
                キャンセル
              </button>
              <button
                className="btn-danger"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? '削除中...' : '削除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
