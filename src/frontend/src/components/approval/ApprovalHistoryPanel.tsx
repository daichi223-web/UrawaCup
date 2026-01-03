/**
 * 承認履歴パネルコンポーネント
 *
 * 試合の承認・却下履歴を表示
 */

import { Clock, Check, X, Calendar, AlertTriangle } from 'lucide-react'
import { clsx } from 'clsx'
import type { MatchWithDetails } from '@shared/types'
import { Card } from '@/components/ui/Card'
import { GroupBadge } from '@/components/ui/Badge'

interface ApprovalHistoryPanelProps {
  /** 試合データ */
  matches: MatchWithDetails[]
  /** 最大表示件数 */
  maxItems?: number
  /** タイトル表示 */
  showTitle?: boolean
}

/**
 * 承認履歴パネル
 */
export function ApprovalHistoryPanel({
  matches,
  maxItems = 10,
  showTitle = true,
}: ApprovalHistoryPanelProps) {
  // 承認済み・却下済みの試合をフィルタしてソート（新しい順）
  const approvalHistory = matches
    .filter((m) => m.approvalStatus && m.approvalStatus !== 'pending')
    .sort((a, b) => {
      if (!a.approvedAt || !b.approvedAt) return 0
      return new Date(b.approvedAt).getTime() - new Date(a.approvedAt).getTime()
    })
    .slice(0, maxItems)

  if (approvalHistory.length === 0) {
    return (
      <Card>
        <div className="flex items-center gap-2 text-gray-500">
          <Clock className="w-5 h-5" />
          <span>承認履歴はありません</span>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      {showTitle && (
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">承認履歴</h3>
        </div>
      )}

      <div className="space-y-3">
        {approvalHistory.map((match) => (
          <ApprovalHistoryItem key={match.id} match={match} />
        ))}
      </div>
    </Card>
  )
}

/**
 * 承認履歴アイテム
 */
function ApprovalHistoryItem({ match }: { match: MatchWithDetails }) {
  const isApproved = match.approvalStatus === 'approved'
  const formatDateTime = (dateStr: string | undefined) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div
      className={clsx(
        'border rounded-lg p-3',
        isApproved
          ? 'border-green-200 bg-green-50'
          : 'border-red-200 bg-red-50'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          {/* ステータスアイコンとチーム名 */}
          <div className="flex items-center gap-2 mb-1">
            {isApproved ? (
              <Check className="w-4 h-4 text-green-600" />
            ) : (
              <X className="w-4 h-4 text-red-600" />
            )}
            <span className="font-medium text-gray-900 text-sm">
              {match.homeTeam?.name} vs {match.awayTeam?.name}
            </span>
          </div>

          {/* スコア */}
          <div className="ml-6 text-sm text-gray-600">
            スコア: {match.homeScoreTotal ?? '-'} - {match.awayScoreTotal ?? '-'}
          </div>

          {/* 承認日時 */}
          <div className="ml-6 flex items-center gap-1 text-xs text-gray-500 mt-1">
            <Calendar className="w-3 h-3" />
            {formatDateTime(match.approvedAt)}
          </div>

          {/* 却下理由（却下時のみ） */}
          {!isApproved && match.rejectionReason && (
            <div className="ml-6 mt-2 flex items-start gap-1 text-xs text-red-600">
              <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>{match.rejectionReason}</span>
            </div>
          )}
        </div>

        {/* グループバッジ */}
        {match.groupId && (
          <GroupBadge group={match.groupId as 'A' | 'B' | 'C' | 'D'} />
        )}
      </div>
    </div>
  )
}

/**
 * 承認ステータスサマリー
 */
interface ApprovalSummaryProps {
  matches: MatchWithDetails[]
}

export function ApprovalSummary({ matches }: ApprovalSummaryProps) {
  const pending = matches.filter((m) => m.approvalStatus === 'pending').length
  const approved = matches.filter((m) => m.approvalStatus === 'approved').length
  const rejected = matches.filter((m) => m.approvalStatus === 'rejected').length
  const noStatus = matches.filter((m) => !m.approvalStatus).length

  return (
    <div className="grid grid-cols-4 gap-4">
      <SummaryCard
        label="未処理"
        count={noStatus}
        color="gray"
        icon={<Clock className="w-5 h-5" />}
      />
      <SummaryCard
        label="承認待ち"
        count={pending}
        color="yellow"
        icon={<AlertTriangle className="w-5 h-5" />}
      />
      <SummaryCard
        label="承認済み"
        count={approved}
        color="green"
        icon={<Check className="w-5 h-5" />}
      />
      <SummaryCard
        label="却下"
        count={rejected}
        color="red"
        icon={<X className="w-5 h-5" />}
      />
    </div>
  )
}

function SummaryCard({
  label,
  count,
  color,
  icon,
}: {
  label: string
  count: number
  color: 'gray' | 'yellow' | 'green' | 'red'
  icon: React.ReactNode
}) {
  const colorClasses = {
    gray: 'bg-gray-100 text-gray-600 border-gray-200',
    yellow: 'bg-yellow-100 text-yellow-600 border-yellow-200',
    green: 'bg-green-100 text-green-600 border-green-200',
    red: 'bg-red-100 text-red-600 border-red-200',
  }

  return (
    <div className={clsx('rounded-lg p-3 border', colorClasses[color])}>
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="mt-2 text-2xl font-bold">{count}</div>
    </div>
  )
}

export default ApprovalHistoryPanel
