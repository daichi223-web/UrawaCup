/**
 * ドラッグ&ドロップで組み合わせ変更可能な試合リスト
 * 研修試合・決勝トーナメントで使用
 */
import { useState, useCallback } from 'react'
import { createPortal } from 'react-dom'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { restrictToWindowEdges } from '@dnd-kit/modifiers'
import {
  useSortable,
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, ArrowLeftRight } from 'lucide-react'
import type { MatchWithDetails } from '@/types'

// ドラッグ可能なチームスロットのID生成
function getSlotId(matchId: number, position: 'home' | 'away') {
  return `${matchId}-${position}`
}

// スロットIDからmatchIdとpositionを取得
function parseSlotId(slotId: string): { matchId: number; position: 'home' | 'away' } {
  const [matchIdStr, position] = slotId.split('-')
  return {
    matchId: parseInt(matchIdStr),
    position: position as 'home' | 'away',
  }
}

interface TeamSlotProps {
  match: MatchWithDetails
  position: 'home' | 'away'
  isDragging?: boolean
}

/**
 * ドラッグ可能なチームスロット
 */
function DraggableTeamSlot({ match, position, isDragging }: TeamSlotProps) {
  const slotId = getSlotId(match.id, position)
  const team = position === 'home' ? match.homeTeam : match.awayTeam
  const teamId = position === 'home' ? match.homeTeamId : match.awayTeamId

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isCurrentlyDragging,
  } = useSortable({ id: slotId })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isCurrentlyDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        flex items-center gap-2 p-2 rounded border-2
        ${isCurrentlyDragging ? 'border-primary-500 bg-primary-50' : 'border-gray-200 bg-white'}
        ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}
        hover:border-primary-300 transition-colors
      `}
      {...attributes}
      {...listeners}
    >
      <GripVertical className="w-4 h-4 text-gray-400" />
      <span className="font-medium truncate flex-1">
        {team?.shortName || team?.name || `チームID: ${teamId}`}
      </span>
    </div>
  )
}

interface DraggableMatchCardProps {
  match: MatchWithDetails
  onSwapTeams?: (matchId: number, homeTeamId: number, awayTeamId: number) => void
}

/**
 * 試合カード（チーム入れ替えボタン付き）
 */
function MatchCardWithSwap({ match, onSwapTeams }: DraggableMatchCardProps) {
  const handleSwap = () => {
    if (onSwapTeams && match.homeTeamId && match.awayTeamId) {
      // ホームとアウェイを入れ替え
      onSwapTeams(match.id, match.awayTeamId, match.homeTeamId)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      scheduled: 'bg-gray-100 text-gray-700',
      in_progress: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
    }
    const labels: Record<string, string> = {
      scheduled: '予定',
      in_progress: '試合中',
      completed: '終了',
    }
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${styles[status] || styles.scheduled}`}>
        {labels[status] || status}
      </span>
    )
  }

  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm text-gray-500">
          #{match.matchOrder} {match.matchTime?.substring(0, 5)}
        </div>
        {getStatusBadge(match.status)}
      </div>

      <div className="flex items-center gap-2">
        {/* ホームチーム */}
        <div className="flex-1 p-2 bg-gray-50 rounded text-center">
          <span className="font-medium">
            {match.homeTeam?.shortName || match.homeTeam?.name || 'TBD'}
          </span>
        </div>

        {/* 入れ替えボタン */}
        <button
          onClick={handleSwap}
          disabled={match.status === 'completed'}
          className={`
            p-2 rounded-full transition-colors
            ${match.status === 'completed'
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-primary-100 text-primary-600 hover:bg-primary-200 cursor-pointer'
            }
          `}
          title="ホーム/アウェイを入れ替え"
        >
          <ArrowLeftRight className="w-5 h-5" />
        </button>

        {/* アウェイチーム */}
        <div className="flex-1 p-2 bg-gray-50 rounded text-center">
          <span className="font-medium">
            {match.awayTeam?.shortName || match.awayTeam?.name || 'TBD'}
          </span>
        </div>
      </div>

      {/* スコア表示（完了時） */}
      {match.status === 'completed' && (
        <div className="mt-3 text-center text-lg font-bold">
          {match.homeScoreTotal} - {match.awayScoreTotal}
        </div>
      )}
    </div>
  )
}

interface DraggableMatchListProps {
  matches: MatchWithDetails[]
  onSwapTeams: (matchId: number, homeTeamId: number, awayTeamId: number) => void
  onSwapMatches?: (match1Id: number, match2Id: number) => void
  title?: string
  emptyMessage?: string
}

/**
 * ドラッグ&ドロップ対応試合リスト
 *
 * 機能:
 * - 試合内のホーム/アウェイチーム入れ替え（ボタンクリック）
 * - 試合間でのチーム交換（ドラッグ&ドロップ）
 */
export default function DraggableMatchList({
  matches,
  onSwapTeams,
  onSwapMatches: _onSwapMatches,
  title = '試合一覧',
  emptyMessage = '試合がありません',
}: DraggableMatchListProps) {
  const [activeId, setActiveId] = useState<string | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor)
  )

  // ドラッグ開始
  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id as string)
  }, [])

  // ドラッグ終了
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event
    setActiveId(null)

    if (!over || active.id === over.id) return

    const activeSlot = parseSlotId(active.id as string)
    const overSlot = parseSlotId(over.id as string)

    // 同じ試合内での入れ替え
    if (activeSlot.matchId === overSlot.matchId) {
      const match = matches.find(m => m.id === activeSlot.matchId)
      if (match && match.homeTeamId && match.awayTeamId) {
        onSwapTeams(match.id, match.awayTeamId, match.homeTeamId)
      }
      return
    }

    // 異なる試合間でのチーム交換
    const match1 = matches.find(m => m.id === activeSlot.matchId)
    const match2 = matches.find(m => m.id === overSlot.matchId)

    if (match1 && match2) {
      // ドラッグ元のチームID
      const team1Id = activeSlot.position === 'home' ? match1.homeTeamId : match1.awayTeamId
      // ドロップ先のチームID
      const team2Id = overSlot.position === 'home' ? match2.homeTeamId : match2.awayTeamId

      if (team1Id && team2Id) {
        // match1の指定位置にteam2を設定
        const newMatch1Home = activeSlot.position === 'home' ? team2Id : match1.homeTeamId
        const newMatch1Away = activeSlot.position === 'away' ? team2Id : match1.awayTeamId

        // match2の指定位置にteam1を設定
        const newMatch2Home = overSlot.position === 'home' ? team1Id : match2.homeTeamId
        const newMatch2Away = overSlot.position === 'away' ? team1Id : match2.awayTeamId

        // 両方の試合を更新
        if (newMatch1Home && newMatch1Away) {
          onSwapTeams(match1.id, newMatch1Home, newMatch1Away)
        }
        if (newMatch2Home && newMatch2Away) {
          onSwapTeams(match2.id, newMatch2Home, newMatch2Away)
        }
      }
    }
  }, [matches, onSwapTeams])

  // ドラッグ中のアイテムを取得
  const getActiveItem = () => {
    if (!activeId) return null
    const slot = parseSlotId(activeId)
    const match = matches.find(m => m.id === slot.matchId)
    if (!match) return null
    const team = slot.position === 'home' ? match.homeTeam : match.awayTeam
    return team?.shortName || team?.name || 'チーム'
  }

  if (matches.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        {emptyMessage}
      </div>
    )
  }

  // ソート可能なIDリストを生成
  const sortableIds = matches.flatMap(m => [
    getSlotId(m.id, 'home'),
    getSlotId(m.id, 'away'),
  ])

  return (
    <div className="space-y-4">
      {title && (
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <div className="text-sm text-gray-500">
            チームをドラッグして入れ替え可能
          </div>
        </div>
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        modifiers={[restrictToWindowEdges]}
      >
        <SortableContext items={sortableIds} strategy={verticalListSortingStrategy}>
          <div className="grid gap-4 md:grid-cols-2">
            {matches.map((match) => (
              <div key={match.id} className="bg-white rounded-lg border-2 border-gray-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm text-gray-500">
                    #{match.matchOrder} {match.matchTime?.substring(0, 5)}
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    match.status === 'completed' ? 'bg-green-100 text-green-800' :
                    match.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {match.status === 'completed' ? '終了' :
                     match.status === 'in_progress' ? '試合中' : '予定'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {/* ホームチーム（ドラッグ可能） */}
                  <div className="flex-1">
                    <DraggableTeamSlot match={match} position="home" />
                  </div>

                  <div className="text-gray-400 font-bold">vs</div>

                  {/* アウェイチーム（ドラッグ可能） */}
                  <div className="flex-1">
                    <DraggableTeamSlot match={match} position="away" />
                  </div>
                </div>

                {/* スコア表示（完了時） */}
                {match.status === 'completed' && (
                  <div className="mt-3 text-center text-lg font-bold">
                    {match.homeScoreTotal} - {match.awayScoreTotal}
                  </div>
                )}
              </div>
            ))}
          </div>
        </SortableContext>

        {createPortal(
          <DragOverlay dropAnimation={null}>
            {activeId && (
              <div className="bg-primary-100 border-2 border-primary-500 rounded p-3 shadow-lg cursor-grabbing">
                <span className="font-medium">{getActiveItem()}</span>
              </div>
            )}
          </DragOverlay>,
          document.body
        )}
      </DndContext>

      <div className="text-xs text-gray-400 text-center mt-4">
        ※ チームをドラッグして別の位置にドロップすると組み合わせが変更されます
      </div>
    </div>
  )
}

export { MatchCardWithSwap }
