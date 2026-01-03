import { useState, useEffect, useMemo, useRef } from 'react';
import api from '@/core/http';
import { Team } from '@shared/types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { Modal } from '@/components/ui/Modal';
import toast from 'react-hot-toast';
import { useImportTeamsCsv } from '@/features/teams/hooks';

// タブの定義
const GROUP_TABS = ['全チーム', 'Aグループ', 'Bグループ', 'Cグループ', 'Dグループ'] as const;
type GroupTab = typeof GROUP_TABS[number];
const GROUP_MAP: Record<GroupTab, string | null> = {
  '全チーム': null,
  'Aグループ': 'A',
  'Bグループ': 'B',
  'Cグループ': 'C',
  'Dグループ': 'D',
};

function TeamManagement() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<GroupTab>('全チーム');
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', groupId: '', teamType: 'invited', isVenueHost: false });
  const [addForm, setAddForm] = useState({ name: '', groupId: '', teamType: 'invited', isVenueHost: false });
  const [saving, setSaving] = useState(false);
  const csvFileInputRef = useRef<HTMLInputElement>(null);
  const importCsvMutation = useImportTeamsCsv();

  // TODO: Context
  const tournamentId = 1;

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const response = await api.get<{ teams: Team[]; total: number }>(`/teams/?tournament_id=${tournamentId}`);
        setTeams(response.data.teams);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchTeams();
  }, [tournamentId]);

  // タブでフィルタリング
  const filteredTeams = useMemo(() => {
    const groupId = GROUP_MAP[activeTab];
    if (!groupId) return teams;
    return teams.filter(t => (t.groupId || t.group_id) === groupId);
  }, [teams, activeTab]);

  // 編集モーダルを開く
  const openEditModal = (team: Team) => {
    setSelectedTeam(team);
    setEditForm({
      name: team.name,
      groupId: team.groupId || team.group_id || '',
      teamType: team.teamType || team.team_type || 'invited',
      isVenueHost: team.isVenueHost ?? team.is_venue_host ?? false,
    });
    setShowEditModal(true);
  };

  // チームを保存
  const handleSave = async () => {
    if (!selectedTeam) return;
    setSaving(true);
    try {
      const { data } = await api.patch<Team>(`/teams/${selectedTeam.id}`, {
        name: editForm.name,
        groupId: editForm.groupId || null,
        teamType: editForm.teamType,
        isVenueHost: editForm.isVenueHost,
      });
      setTeams(prev => prev.map(t => t.id === selectedTeam.id ? data : t));
      setShowEditModal(false);
      toast.success('チーム情報を更新しました');
    } catch (error) {
      const message = error instanceof Error ? error.message : '更新に失敗しました';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  // 新規チームを追加
  const handleAddTeam = async () => {
    if (!addForm.name.trim()) {
      toast.error('チーム名を入力してください');
      return;
    }
    setSaving(true);
    try {
      const { data } = await api.post<Team>('/teams/', {
        name: addForm.name,
        tournamentId: tournamentId,
        groupId: addForm.groupId || null,
        teamType: addForm.teamType,
        isVenueHost: addForm.isVenueHost,
      });
      setTeams(prev => [...prev, data]);
      setShowAddModal(false);
      setAddForm({ name: '', groupId: '', teamType: 'invited', isVenueHost: false });
      toast.success('チームを追加しました');
    } catch (error) {
      const message = error instanceof Error ? error.message : '追加に失敗しました';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  // CSVインポート処理
  const handleCsvImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    try {
      const result = await importCsvMutation.mutateAsync({ tournamentId, file });
      toast.success(`${result.imported}チームをインポートしました`);
      // チーム一覧を再取得
      const response = await api.get<{ teams: Team[]; total: number }>(`/teams/?tournament_id=${tournamentId}`);
      setTeams(response.data.teams);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'インポートに失敗しました';
      toast.error(message);
    } finally {
      // ファイル入力をリセット
      if (csvFileInputRef.current) {
        csvFileInputRef.current.value = '';
      }
    }
  };

  if (loading) return <LoadingSpinner />;
  return (
    <div className="space-y-6">
      {/* ページヘッダー */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">チーム管理</h1>
          <p className="text-gray-600 mt-1">
            参加チームの登録・編集・グループ分けを行います
          </p>
        </div>
        <div className="flex gap-2">
          <input
            ref={csvFileInputRef}
            type="file"
            accept=".csv"
            onChange={handleCsvImport}
            className="hidden"
          />
          <button 
            className="btn-secondary" 
            onClick={() => csvFileInputRef.current?.click()}
            disabled={importCsvMutation.isPending}
          >
            {importCsvMutation.isPending ? 'インポート中...' : 'CSVインポート'}
          </button>
          <button className="btn-primary" onClick={() => setShowAddModal(true)}>チーム追加</button>
        </div>
      </div>

      {/* グループタブ */}
      <div className="card">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {GROUP_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab}
                {activeTab === tab && filteredTeams.length > 0 && (
                  <span className="ml-2 bg-primary-100 text-primary-700 text-xs px-2 py-0.5 rounded-full">
                    {filteredTeams.length}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* チーム一覧テーブル */}
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>グループ</th>
                <th>番号</th>
                <th>チーム名</th>
                <th>区分</th>
                <th>会場担当</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>

              {filteredTeams.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    チームが登録されていません
                  </td>
                </tr>
              ) : (
                filteredTeams.map((team) => (
                  <tr key={team.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {(() => {
                        const gid = team.groupId || team.group_id;
                        return (
                          <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold
                            ${gid === 'A' ? 'bg-red-100 text-red-800' :
                              gid === 'B' ? 'bg-blue-100 text-blue-800' :
                                gid === 'C' ? 'bg-green-100 text-green-800' :
                                  gid === 'D' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                            {gid || '-'}
                          </span>
                        );
                      })()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">#{team.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-lg font-bold text-gray-900">{team.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {(team.teamType || team.team_type) === 'local' ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          地元
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          招待
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(team.isVenueHost || team.is_venue_host) ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          会場校
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        onClick={() => openEditModal(team)}
                      >
                        編集
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 編集モーダル */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="チーム編集"
      >
        <div className="space-y-4">
          <div>
            <label className="form-label">チーム名</label>
            <input
              type="text"
              className="form-input"
              value={editForm.name}
              onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="form-label">グループ</label>
            <select
              className="form-input"
              value={editForm.groupId}
              onChange={(e) => setEditForm(prev => ({ ...prev, groupId: e.target.value }))}
            >
              <option value="">未設定</option>
              <option value="A">Aグループ</option>
              <option value="B">Bグループ</option>
              <option value="C">Cグループ</option>
              <option value="D">Dグループ</option>
            </select>
          </div>
          <div>
            <label className="form-label">チーム区分</label>
            <select
              className="form-input"
              value={editForm.teamType}
              onChange={(e) => setEditForm(prev => ({ ...prev, teamType: e.target.value }))}
            >
              <option value="invited">招待チーム</option>
              <option value="local">地元チーム</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isVenueHost"
              checked={editForm.isVenueHost}
              onChange={(e) => setEditForm(prev => ({ ...prev, isVenueHost: e.target.checked }))}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="isVenueHost" className="text-sm text-gray-700">
              会場担当チーム
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowEditModal(false)}
            >
              キャンセル
            </button>
            <button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </Modal>

      {/* チーム追加モーダル */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="チーム追加"
      >
        <div className="space-y-4">
          <div>
            <label className="form-label">チーム名 *</label>
            <input
              type="text"
              className="form-input"
              value={addForm.name}
              onChange={(e) => setAddForm(prev => ({ ...prev, name: e.target.value }))}
              placeholder="チーム名を入力"
            />
          </div>
          <div>
            <label className="form-label">グループ</label>
            <select
              className="form-input"
              value={addForm.groupId}
              onChange={(e) => setAddForm(prev => ({ ...prev, groupId: e.target.value }))}
            >
              <option value="">未設定</option>
              <option value="A">Aグループ</option>
              <option value="B">Bグループ</option>
              <option value="C">Cグループ</option>
              <option value="D">Dグループ</option>
            </select>
          </div>
          <div>
            <label className="form-label">チーム区分</label>
            <select
              className="form-input"
              value={addForm.teamType}
              onChange={(e) => setAddForm(prev => ({ ...prev, teamType: e.target.value }))}
            >
              <option value="invited">招待チーム</option>
              <option value="local">地元チーム</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="addIsVenueHost"
              checked={addForm.isVenueHost}
              onChange={(e) => setAddForm(prev => ({ ...prev, isVenueHost: e.target.checked }))}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="addIsVenueHost" className="text-sm text-gray-700">
              会場担当チーム
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowAddModal(false)}
            >
              キャンセル
            </button>
            <button
              className="btn-primary"
              onClick={handleAddTeam}
              disabled={saving}
            >
              {saving ? '追加中...' : '追加'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default TeamManagement
