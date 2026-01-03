/**
 * 設定画面
 * 大会設定・会場設定・選手管理
 */
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/core/http'
import { Modal } from '@/components/ui/Modal'
import type { Venue, Tournament } from '@/types'
import { useCreateVenue } from '@/features/venues/hooks'
import { useCreateTournament } from '@/features/tournaments/hooks'
import { useAppStore } from '@/stores/appStore'

// グループの色設定
const GROUP_COLORS: Record<string, string> = {
  A: 'bg-red-100 text-red-800',
  B: 'bg-blue-100 text-blue-800',
  C: 'bg-green-100 text-green-800',
  D: 'bg-yellow-100 text-yellow-800',
}

function Settings() {
  const queryClient = useQueryClient()
  const setCurrentTournament = useAppStore(state => state.setCurrentTournament)
  const tournamentId = 1 // TODO: コンテキストから取得

  // 大会設定フォーム
  const [tournamentForm, setTournamentForm] = useState({
    name: '',
    shortName: '',
    edition: 0,
    startDate: '',
    endDate: '',
    matchDuration: 50,
    intervalMinutes: 15,
  })

  // 会場編集モーダル
  const [showVenueModal, setShowVenueModal] = useState(false)
  const [selectedVenue, setSelectedVenue] = useState<Venue | null>(null)
  const [venueForm, setVenueForm] = useState({
    name: '',
    address: '',
    groupId: '',
    maxMatchesPerDay: 6,
  })
  const [showAddVenueModal, setShowAddVenueModal] = useState(false)
  const [addVenueForm, setAddVenueForm] = useState({
    name: '',
    shortName: '',
    address: '',
    groupId: '',
    pitchCount: 1,
  })

  // 新規大会作成モーダル
  const [showNewTournamentModal, setShowNewTournamentModal] = useState(false)
  const [newTournamentForm, setNewTournamentForm] = useState({
    name: '',
    shortName: '',
    edition: 1,
    year: new Date().getFullYear(),
    startDate: '',
    endDate: '',
    matchDuration: 50,
    halfDuration: 25,
    intervalMinutes: 15,
  })

  // 大会情報を取得
  const { data: tournament } = useQuery({
    queryKey: ['tournament', tournamentId],
    queryFn: async () => {
      const { data } = await api.get<Tournament>(`/tournaments/${tournamentId}`)
      return data
    },
  })

  // 大会情報が取得できたらフォームを初期化
  useEffect(() => {
    if (tournament) {
      setTournamentForm({
        name: tournament.name || '',
        shortName: tournament.shortName || '',
        edition: tournament.edition || 0,
        startDate: tournament.startDate || '',
        endDate: tournament.endDate || '',
        matchDuration: tournament.matchDuration || 50,
        intervalMinutes: tournament.intervalMinutes || 15,
      })
    }
  }, [tournament])

  // 大会設定更新
  const updateTournamentMutation = useMutation({
    mutationFn: async (data: {
      name: string;
      shortName: string;
      edition: number;
      startDate: string;
      endDate: string;
      matchDuration: number;
      intervalMinutes: number;
    }) => {
      const response = await api.patch<Tournament>(`/tournaments/${tournamentId}`, {
        name: data.name,
        short_name: data.shortName,
        edition: data.edition,
        start_date: data.startDate,
        end_date: data.endDate,
        match_duration: data.matchDuration,
        interval_minutes: data.intervalMinutes,
      })
      return response.data
    },
    onSuccess: (updatedTournament) => {
      queryClient.invalidateQueries({ queryKey: ['tournament', tournamentId] })
      setCurrentTournament(updatedTournament)
      toast.success('大会設定を更新しました')
    },
    onError: (error: Error) => {
      toast.error(`更新に失敗しました: ${error.message}`)
    },
  })

  // 大会設定を保存
  const handleSaveTournament = () => {
    updateTournamentMutation.mutate(tournamentForm)
  }

  // 会場一覧を取得
  const { data: venueData, isLoading: isLoadingVenues } = useQuery({
    queryKey: ['venues', tournamentId],
    queryFn: async () => {
      const { data } = await api.get<{ venues: Venue[]; total: number }>(`/venues?tournament_id=${tournamentId}`)
      return data
    },
  })
  const venues = venueData?.venues ?? []


  // 大会作成
  const createTournamentMutation = useCreateTournament()

  // 会場作成
  const createVenueMutation = useCreateVenue()

  // 会場更新
  const updateVenueMutation = useMutation({
    mutationFn: async (data: { id: number; name: string; address?: string; group_id?: string; max_matches_per_day?: number }) => {
      const { id, ...rest } = data
      const response = await api.patch<Venue>(`/venues/${id}`, rest)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['venues', tournamentId] })
      setShowVenueModal(false)
      toast.success('会場情報を更新しました')
    },
    onError: (error: Error) => {
      toast.error(`更新に失敗しました: ${error.message}`)
    },
  })

  // 会場編集モーダルを開く
  const openVenueModal = (venue: Venue) => {
    setSelectedVenue(venue)
    setVenueForm({
      name: venue.name,
      address: venue.address || '',
      groupId: venue.groupId || venue.group_id || '',
      maxMatchesPerDay: venue.maxMatchesPerDay ?? venue.max_matches_per_day ?? 6,
    })
    setShowVenueModal(true)
  }

  // 会場を保存
  const handleSaveVenue = () => {
    if (!selectedVenue) return
    updateVenueMutation.mutate({
      id: selectedVenue.id,
      name: venueForm.name,
      address: venueForm.address || undefined,
      group_id: venueForm.groupId || undefined,
      max_matches_per_day: venueForm.maxMatchesPerDay,
    })
  }

  // 新規大会を作成
  const handleCreateTournament = () => {
    if (!newTournamentForm.name.trim()) {
      toast.error('大会名を入力してください')
      return
    }
    if (!newTournamentForm.startDate || !newTournamentForm.endDate) {
      toast.error('開始日と終了日を入力してください')
      return
    }
    createTournamentMutation.mutate(
      {
        name: newTournamentForm.name,
        shortName: newTournamentForm.shortName || undefined,
        edition: newTournamentForm.edition,
        year: newTournamentForm.year,
        startDate: newTournamentForm.startDate,
        endDate: newTournamentForm.endDate,
        matchDuration: newTournamentForm.matchDuration,
        halfDuration: newTournamentForm.halfDuration,
        intervalMinutes: newTournamentForm.intervalMinutes,
      },
      {
        onSuccess: (newTournament) => {
          setShowNewTournamentModal(false)
          setNewTournamentForm({
            name: '',
            shortName: '',
            edition: 1,
            year: new Date().getFullYear(),
            startDate: '',
            endDate: '',
            matchDuration: 50,
            halfDuration: 25,
            intervalMinutes: 15,
          })
          toast.success(`大会「${newTournament.name}」を作成しました`)
          // TODO: 作成した大会に切り替える
        },
        onError: (error: Error) => {
          toast.error(`作成に失敗しました: ${error.message}`)
        },
      }
    )
  }

  // 会場を追加
  const handleAddVenue = () => {
    if (!addVenueForm.name.trim()) {
      toast.error('会場名を入力してください')
      return
    }
    createVenueMutation.mutate(
      {
        tournamentId,
        name: addVenueForm.name,
        shortName: addVenueForm.shortName || addVenueForm.name,
        address: addVenueForm.address || undefined,
        groupId: addVenueForm.groupId || undefined,
        pitchCount: addVenueForm.pitchCount,
      },
      {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['venues', tournamentId] })
          setShowAddVenueModal(false)
          setAddVenueForm({ name: '', shortName: '', address: '', groupId: '', pitchCount: 1 })
          toast.success('会場を追加しました')
        },
        onError: (error: Error) => {
          toast.error(`追加に失敗しました: ${error.message}`)
        },
      }
    )
  }

  return (
    <div className="space-y-6">
      {/* ページヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">設定</h1>
          <p className="text-gray-600 mt-1">
            大会の基本設定を行います
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowNewTournamentModal(true)}
        >
          + 新規大会作成
        </button>
      </div>

      {/* 大会設定 */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">大会設定</h3>
        </div>
        <div className="card-body space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label">大会名</label>
              <input
                type="text"
                className="form-input"
                value={tournamentForm.name}
                placeholder="浦和カップ高校サッカーフェスティバル"
                onChange={(e) => setTournamentForm(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="form-label">略称 (Short Name)</label>
              <input
                type="text"
                className="form-input"
                value={tournamentForm.shortName}
                placeholder="浦和カップ2026"
                onChange={(e) => setTournamentForm(prev => ({ ...prev, shortName: e.target.value }))}
              />
            </div>
            <div>
              <label className="form-label">回数</label>
              <input
                type="number"
                className="form-input"
                value={tournamentForm.edition}
                placeholder="35"
                onChange={(e) => setTournamentForm(prev => ({ ...prev, edition: parseInt(e.target.value) || 0 }))}
              />
            </div>
            <div>
              <label className="form-label">開始日</label>
              <input
                type="date"
                className="form-input"
                value={tournamentForm.startDate}
                onChange={(e) => setTournamentForm(prev => ({ ...prev, startDate: e.target.value }))}
              />
            </div>
            <div>
              <label className="form-label">終了日</label>
              <input
                type="date"
                className="form-input"
                value={tournamentForm.endDate}
                onChange={(e) => setTournamentForm(prev => ({ ...prev, endDate: e.target.value }))}
              />
            </div>
            <div>
              <label className="form-label">試合時間（分）</label>
              <input
                type="number"
                className="form-input"
                value={tournamentForm.matchDuration}
                placeholder="50"
                onChange={(e) => setTournamentForm(prev => ({ ...prev, matchDuration: parseInt(e.target.value) || 50 }))}
              />
            </div>
            <div>
              <label className="form-label">試合間隔（分）</label>
              <input
                type="number"
                className="form-input"
                value={tournamentForm.intervalMinutes}
                placeholder="15"
                onChange={(e) => setTournamentForm(prev => ({ ...prev, intervalMinutes: parseInt(e.target.value) || 15 }))}
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button
              className="btn-primary"
              onClick={handleSaveTournament}
              disabled={updateTournamentMutation.isPending}
            >
              {updateTournamentMutation.isPending ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>

      {/* 会場設定 */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <h3 className="text-lg font-semibold">会場設定</h3>
          <button className="btn-secondary text-sm" onClick={() => setShowAddVenueModal(true)}>会場追加</button>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>会場名</th>
                <th>担当グループ</th>
                <th>住所</th>
                <th>1日あたりの試合数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {isLoadingVenues ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-500">
                    読み込み中...
                  </td>
                </tr>
              ) : venues.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-500">
                    会場が登録されていません
                  </td>
                </tr>
              ) : (
                venues.map((venue) => (
                  <tr key={venue.id}>
                    <td>{venue.name}</td>
                    <td>
                      {(venue.group_id || venue.groupId) ? (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${GROUP_COLORS[venue.group_id || venue.groupId || ''] || 'bg-gray-100 text-gray-800'}`}>
                          {venue.group_id || venue.groupId}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>{venue.address || '-'}</td>
                    <td>{venue.maxMatchesPerDay ?? venue.max_matches_per_day}</td>
                    <td>
                      <button
                        className="text-primary-600 hover:text-primary-800 text-sm"
                        onClick={() => openVenueModal(venue)}
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

      {/* 選手データ管理 */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">選手データ管理</h3>
        </div>
        <div className="card-body">
          <p className="text-gray-600 mb-4">
            各チームの選手データをCSV/Excel形式でインポートできます。
            インポートした選手名は、得点者入力時のサジェストに使用されます。
          </p>
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={() => toast.error('テンプレートダウンロード機能は準備中です')}>
              テンプレートダウンロード
            </button>
            <button className="btn-primary" onClick={() => toast.error('選手データインポート機能は準備中です')}>
              選手データインポート
            </button>
          </div>
        </div>
      </div>

      {/* 新規大会作成モーダル */}
      <Modal
        isOpen={showNewTournamentModal}
        onClose={() => setShowNewTournamentModal(false)}
        title="新規大会作成"
      >
        <div className="space-y-4">
          <div>
            <label className="form-label">大会名 *</label>
            <input
              type="text"
              className="form-input"
              value={newTournamentForm.name}
              onChange={(e) => setNewTournamentForm(prev => ({ ...prev, name: e.target.value }))}
              placeholder="浦和カップ高校サッカーフェスティバル"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">略称</label>
              <input
                type="text"
                className="form-input"
                value={newTournamentForm.shortName}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, shortName: e.target.value }))}
                placeholder="浦和カップ2026"
              />
            </div>
            <div>
              <label className="form-label">回数（第○回）</label>
              <input
                type="number"
                className="form-input"
                min={1}
                value={newTournamentForm.edition}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, edition: parseInt(e.target.value) || 1 }))}
              />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="form-label">開催年度</label>
              <input
                type="number"
                className="form-input"
                min={2000}
                max={2100}
                value={newTournamentForm.year}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, year: parseInt(e.target.value) || new Date().getFullYear() }))}
              />
            </div>
            <div>
              <label className="form-label">開始日 *</label>
              <input
                type="date"
                className="form-input"
                value={newTournamentForm.startDate}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, startDate: e.target.value }))}
              />
            </div>
            <div>
              <label className="form-label">終了日 *</label>
              <input
                type="date"
                className="form-input"
                value={newTournamentForm.endDate}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, endDate: e.target.value }))}
              />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="form-label">試合時間（分）</label>
              <input
                type="number"
                className="form-input"
                min={10}
                max={120}
                value={newTournamentForm.matchDuration}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, matchDuration: parseInt(e.target.value) || 50 }))}
              />
            </div>
            <div>
              <label className="form-label">ハーフタイム（分）</label>
              <input
                type="number"
                className="form-input"
                min={5}
                max={60}
                value={newTournamentForm.halfDuration}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, halfDuration: parseInt(e.target.value) || 25 }))}
              />
            </div>
            <div>
              <label className="form-label">試合間隔（分）</label>
              <input
                type="number"
                className="form-input"
                min={5}
                max={60}
                value={newTournamentForm.intervalMinutes}
                onChange={(e) => setNewTournamentForm(prev => ({ ...prev, intervalMinutes: parseInt(e.target.value) || 15 }))}
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowNewTournamentModal(false)}
            >
              キャンセル
            </button>
            <button
              className="btn-primary"
              onClick={handleCreateTournament}
              disabled={createTournamentMutation.isPending}
            >
              {createTournamentMutation.isPending ? '作成中...' : '作成'}
            </button>
          </div>
        </div>
      </Modal>

      {/* 会場追加モーダル */}
      <Modal
        isOpen={showAddVenueModal}
        onClose={() => setShowAddVenueModal(false)}
        title="会場追加"
      >
        <div className="space-y-4">
          <div>
            <label className="form-label">会場名 *</label>
            <input
              type="text"
              className="form-input"
              value={addVenueForm.name}
              onChange={(e) => setAddVenueForm(prev => ({ ...prev, name: e.target.value }))}
              placeholder="浦和南高校グラウンド"
            />
          </div>
          <div>
            <label className="form-label">略称</label>
            <input
              type="text"
              className="form-input"
              value={addVenueForm.shortName}
              onChange={(e) => setAddVenueForm(prev => ({ ...prev, shortName: e.target.value }))}
              placeholder="浦和南"
            />
          </div>
          <div>
            <label className="form-label">住所</label>
            <input
              type="text"
              className="form-input"
              value={addVenueForm.address}
              onChange={(e) => setAddVenueForm(prev => ({ ...prev, address: e.target.value }))}
              placeholder="さいたま市南区..."
            />
          </div>
          <div>
            <label className="form-label">担当グループ</label>
            <select
              className="form-input"
              value={addVenueForm.groupId}
              onChange={(e) => setAddVenueForm(prev => ({ ...prev, groupId: e.target.value }))}
            >
              <option value="">未設定</option>
              <option value="A">Aグループ</option>
              <option value="B">Bグループ</option>
              <option value="C">Cグループ</option>
              <option value="D">Dグループ</option>
            </select>
          </div>
          <div>
            <label className="form-label">コート数</label>
            <input
              type="number"
              className="form-input"
              min={1}
              max={4}
              value={addVenueForm.pitchCount}
              onChange={(e) => setAddVenueForm(prev => ({ ...prev, pitchCount: parseInt(e.target.value) || 1 }))}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowAddVenueModal(false)}
            >
              キャンセル
            </button>
            <button
              className="btn-primary"
              onClick={handleAddVenue}
              disabled={createVenueMutation.isPending}
            >
              {createVenueMutation.isPending ? '追加中...' : '追加'}
            </button>
          </div>
        </div>
      </Modal>

      {/* 会場編集モーダル */}
      <Modal
        isOpen={showVenueModal}
        onClose={() => setShowVenueModal(false)}
        title="会場編集"
      >
        <div className="space-y-4">
          <div>
            <label className="form-label">会場名</label>
            <input
              type="text"
              className="form-input"
              value={venueForm.name}
              onChange={(e) => setVenueForm(prev => ({ ...prev, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="form-label">住所</label>
            <input
              type="text"
              className="form-input"
              value={venueForm.address}
              onChange={(e) => setVenueForm(prev => ({ ...prev, address: e.target.value }))}
            />
          </div>
          <div>
            <label className="form-label">担当グループ</label>
            <select
              className="form-input"
              value={venueForm.groupId}
              onChange={(e) => setVenueForm(prev => ({ ...prev, groupId: e.target.value }))}
            >
              <option value="">未設定</option>
              <option value="A">Aグループ</option>
              <option value="B">Bグループ</option>
              <option value="C">Cグループ</option>
              <option value="D">Dグループ</option>
            </select>
          </div>
          <div>
            <label className="form-label">1日あたりの試合数</label>
            <input
              type="number"
              className="form-input"
              min={1}
              max={12}
              value={venueForm.maxMatchesPerDay}
              onChange={(e) => setVenueForm(prev => ({ ...prev, maxMatchesPerDay: parseInt(e.target.value) || 6 }))}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              className="btn-secondary"
              onClick={() => setShowVenueModal(false)}
            >
              キャンセル
            </button>
            <button
              className="btn-primary"
              onClick={handleSaveVenue}
              disabled={updateVenueMutation.isPending}
            >
              {updateVenueMutation.isPending ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default Settings
