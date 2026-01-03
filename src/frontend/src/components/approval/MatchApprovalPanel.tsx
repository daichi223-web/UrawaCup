/**
 * 試合結果承認パネルコンポーネント
 *
 * 承認待ち試合の一覧表示、承認・却下機能を提供
 */

import { useState, useEffect } from 'react'
import { Check, X, AlertTriangle, Clock, User, MapPin, Calendar } from 'lucide-react'
import { clsx } from 'clsx'
import type { MatchWithDetails } from '@shared/types'
import { useMatchStore } from '@/stores/matchStore'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { ApprovalStatusBadge, MatchStatusBadge, GroupBadge } from '@/components/ui/Badge'

interface MatchApprovalPanelProps {
  /** 大会ID */
  tournamentId?: number
  /** 会場ID（会場担当者の場合） */
  venueId?: number
  /** コンパクト表示 */
  compact?: boolean
}

/**
 * 試合結果承認パネル
 */
export function MatchApprovalPanel({
  tournamentId,
  venueId,
  compact = false
}: MatchApprovalPanelProps) {
  const { user } = useAuthStore()
  const {
    pendingApprovalMatches,
    pendingApprovalCount,
    isLoading,
    fetchPendingApprovalMatches,
    approveMatch,
    rejectMatch
  } = useMatchStore()

  // 却下モーダルの状態
  const [rejectModalOpen, setRejectModalOpen] = useState(false)
  const [selectedMatch, setSelectedMatch] = useState<MatchWithDetails | null>(null)
  const [rejectReason, setRejectReason] = useState('')

  // 詳細モーダルの状態
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [detailMatch, setDetailMatch] = useState<MatchWithDetails | null>(null)

  // データ取得
  useEffect(() => {
    fetchPendingApprovalMatches(tournamentId, venueId)
  }, [fetchPendingApprovalMatches, tournamentId, venueId])

  // 管理者チェック
  const isAdmin = user?.role === 'admin'

  // 承認処理
  const handleApprove = async (match: MatchWithDetails) => {
    if (!user) return
    await approveMatch(match.id, user.id)
  }

  // 却下モーダルを開く
  const handleOpenRejectModal = (match: MatchWithDetails) => {
    setSelectedMatch(match)
    setRejectReason('')
    setRejectModalOpen(true)
  }

  // 却下処理
  const handleReject = async () => {
    if (!user || !selectedMatch || !rejectReason.trim()) return

    const success = await rejectMatch(selectedMatch.id, user.id, rejectReason.trim())
    if (success) {
      setRejectModalOpen(false)
      setSelectedMatch(null)
      setRejectReason('')
    }
  }

  // 詳細表示
  const handleShowDetail = (match: MatchWithDetails) => {
    setDetailMatch(match)
    setDetailModalOpen(true)
  }

  if (pendingApprovalCount === 0 && !isLoading) {
    return (
      <Card className={clsx(compact && 'p-3')}>
        <div className="flex items-center gap-2 text-gray-500">
          <Check className="w-5 h-5 text-green-500" />
          <span>承認待ちの試合はありません</span>
        </div>
      </Card>
    )
  }

  return (
    <>
      <Card className={clsx(compact && 'p-3')}>
        {/* ヘッダー */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-yellow-500" />
            <h3 className="font-semibold text-gray-900">
              承認待ち ({pendingApprovalCount})
            </h3>
          </div>
        </div>

        {/* 試合一覧 */}
        <div className="space-y-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
            </div>
          ) : (
            pendingApprovalMatches.map((match) => (
              <MatchApprovalCard
                key={match.id}
                match={match}
                isAdmin={isAdmin}
                compact={compact}
                onApprove={handleApprove}
                onReject={handleOpenRejectModal}
                onShowDetail={handleShowDetail}
              />
            ))
          )}
        </div>
      </Card>

      {/* 却下理由モーダル */}
      <Modal
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title="試合結果を却下"
        size="md"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setRejectModalOpen(false)}
            >
              キャンセル
            </Button>
            <Button
              variant="danger"
              onClick={handleReject}
              disabled={!rejectReason.trim()}
              isLoading={isLoading}
            >
              却下する
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {selectedMatch && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="font-medium">
                {selectedMatch.homeTeam?.name} vs {selectedMatch.awayTeam?.name}
              </div>
              <div className="text-sm text-gray-500 mt-1">
                スコア: {selectedMatch.homeScoreTotal ?? '-'} - {selectedMatch.awayScoreTotal ?? '-'}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              却下理由 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="却下の理由を入力してください..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              rows={3}
            />
            <p className="mt-1 text-xs text-gray-500">
              会場担当者に再入力を依頼するため、具体的な理由を記入してください
            </p>
          </div>
        </div>
      </Modal>

      {/* 詳細モーダル */}
      <MatchDetailModal
        isOpen={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        match={detailMatch}
        isAdmin={isAdmin}
        onApprove={handleApprove}
        onReject={handleOpenRejectModal}
      />
    </>
  )
}

/**
 * 試合承認カード
 */
interface MatchApprovalCardProps {
  match: MatchWithDetails
  isAdmin: boolean
  compact: boolean
  onApprove: (match: MatchWithDetails) => void
  onReject: (match: MatchWithDetails) => void
  onShowDetail: (match: MatchWithDetails) => void
}

function MatchApprovalCard({
  match,
  isAdmin,
  compact,
  onApprove,
  onReject,
  onShowDetail,
}: MatchApprovalCardProps) {
  const formatTime = (time: string) => {
    return time.substring(0, 5) // HH:mm形式
  }

  return (
    <div
      className={clsx(
        'border border-yellow-200 bg-yellow-50 rounded-lg p-3',
        'hover:bg-yellow-100 transition-colors cursor-pointer'
      )}
      onClick={() => onShowDetail(match)}
    >
      {/* 試合情報 */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* グループ・会場 */}
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
            {match.groupId && <GroupBadge group={match.groupId as 'A' | 'B' | 'C' | 'D'} />}
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {match.venue?.name}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatTime(match.matchTime)}
            </span>
          </div>

          {/* チーム名とスコア */}
          <div className="font-medium text-gray-900">
            {match.homeTeam?.name ?? '未定'}
            <span className="mx-2 text-lg font-bold text-primary-600">
              {match.homeScoreTotal ?? '-'} - {match.awayScoreTotal ?? '-'}
            </span>
            {match.awayTeam?.name ?? '未定'}
          </div>

          {/* 入力者情報 */}
          {!compact && (
            <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
              <User className="w-3 h-3" />
              <span>
                入力: {match.enteredAt ? new Date(match.enteredAt).toLocaleString('ja-JP') : '-'}
              </span>
            </div>
          )}
        </div>

        {/* アクションボタン */}
        {isAdmin && (
          <div
            className="flex items-center gap-2"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => onApprove(match)}
              className="p-2 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
              title="承認"
            >
              <Check className="w-5 h-5" />
            </button>
            <button
              onClick={() => onReject(match)}
              className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
              title="却下"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * 試合詳細モーダル
 */
interface MatchDetailModalProps {
  isOpen: boolean
  onClose: () => void
  match: MatchWithDetails | null
  isAdmin: boolean
  onApprove: (match: MatchWithDetails) => void
  onReject: (match: MatchWithDetails) => void
}

function MatchDetailModal({
  isOpen,
  onClose,
  match,
  isAdmin,
  onApprove,
  onReject,
}: MatchDetailModalProps) {
  if (!match) return null

  const handleApprove = () => {
    onApprove(match)
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="試合結果詳細"
      size="lg"
      footer={
        isAdmin && match.approvalStatus === 'pending' ? (
          <>
            <Button variant="ghost" onClick={onClose}>
              閉じる
            </Button>
            <Button
              variant="danger"
              onClick={() => {
                onClose()
                onReject(match)
              }}
              leftIcon={<X className="w-4 h-4" />}
            >
              却下
            </Button>
            <Button
              variant="primary"
              onClick={handleApprove}
              leftIcon={<Check className="w-4 h-4" />}
            >
              承認
            </Button>
          </>
        ) : (
          <Button variant="ghost" onClick={onClose}>
            閉じる
          </Button>
        )
      }
    >
      <div className="space-y-4">
        {/* ステータス */}
        <div className="flex items-center gap-2">
          <MatchStatusBadge status={match.status} />
          <ApprovalStatusBadge status={match.approvalStatus} />
        </div>

        {/* スコア */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-center gap-4">
            <div className="text-right flex-1">
              <div className="font-bold text-lg">{match.homeTeam?.name}</div>
              {match.groupId && (
                <div className="text-sm text-gray-500">
                  {match.groupId}組{match.homeTeam?.groupOrder}番
                </div>
              )}
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-primary-600">
                {match.homeScoreTotal ?? '-'} - {match.awayScoreTotal ?? '-'}
              </div>
              <div className="text-sm text-gray-500 mt-1">
                (前半 {match.homeScoreHalf1 ?? '-'} - {match.awayScoreHalf1 ?? '-'})
                (後半 {match.homeScoreHalf2 ?? '-'} - {match.awayScoreHalf2 ?? '-'})
              </div>
              {match.hasPenaltyShootout && (
                <div className="text-sm text-red-600 mt-1">
                  PK {match.homePK ?? '-'} - {match.awayPK ?? '-'}
                </div>
              )}
            </div>
            <div className="text-left flex-1">
              <div className="font-bold text-lg">{match.awayTeam?.name}</div>
              {match.groupId && (
                <div className="text-sm text-gray-500">
                  {match.groupId}組{match.awayTeam?.groupOrder}番
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 得点情報 */}
        {match.goals && match.goals.length > 0 && (
          <div>
            <h4 className="font-medium text-gray-900 mb-2">得点経過</h4>
            <div className="space-y-1">
              {match.goals.map((goal, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 text-sm"
                >
                  <span className="text-gray-500 w-12">
                    {goal.half === 1 ? '前半' : '後半'} {goal.minute}'
                  </span>
                  <span className={clsx(
                    'font-medium',
                    goal.teamId === match.homeTeamId ? 'text-blue-600' : 'text-red-600'
                  )}>
                    {goal.playerName}
                  </span>
                  {goal.isOwnGoal && <span className="text-xs text-gray-500">(OG)</span>}
                  {goal.isPenalty && <span className="text-xs text-gray-500">(PK)</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 試合情報 */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">試合日時:</span>
            <span className="ml-2">
              {new Date(match.matchDate).toLocaleDateString('ja-JP')} {match.matchTime}
            </span>
          </div>
          <div>
            <span className="text-gray-500">会場:</span>
            <span className="ml-2">{match.venue?.name}</span>
          </div>
          <div>
            <span className="text-gray-500">入力日時:</span>
            <span className="ml-2">
              {match.enteredAt ? new Date(match.enteredAt).toLocaleString('ja-JP') : '-'}
            </span>
          </div>
        </div>

        {/* 却下理由（却下時のみ） */}
        {match.approvalStatus === 'rejected' && match.rejectionReason && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-medium text-red-700">却下理由</div>
                <div className="text-sm text-red-600 mt-1">{match.rejectionReason}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default MatchApprovalPanel
