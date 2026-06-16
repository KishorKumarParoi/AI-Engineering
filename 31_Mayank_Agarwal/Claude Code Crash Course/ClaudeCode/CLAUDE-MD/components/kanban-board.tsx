'use client'

import { useState, useCallback } from 'react'
import type { JobApplication } from '@/types'
import { DragDropContext, DropResult } from '@hello-pangea/dnd'
import { useJobApplications } from '@/lib/context'
import { KanbanColumn } from './kanban-column'
import { Spinner } from './ui/spinner'

interface KanbanBoardProps {
  onEditApplication: (app: JobApplication) => void
  onAddApplication: (status: string) => void
}

export function KanbanBoard({ onEditApplication, onAddApplication }: KanbanBoardProps) {
  const { boardData, isLoading, moveApplication } = useJobApplications()
  const [isMoving, setIsMoving] = useState(false)

  const handleDragEnd = useCallback(
    async (result: DropResult) => {
      const { source, destination, draggableId } = result

      if (!destination) {
        return
      }

      if (
        source.droppableId === destination.droppableId &&
        source.index === destination.index
      ) {
        return
      }

      const app = boardData.columns
        .flatMap((col) => col.applications)
        .find((a) => a.id === draggableId)

      if (!app) return

      setIsMoving(true)
      try {
        await moveApplication(
          draggableId,
          destination.droppableId as any,
          destination.index,
        )
      } catch (err) {
        console.error('Failed to move application:', err)
      } finally {
        setIsMoving(false)
      }
    },
    [boardData, moveApplication],
  )

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-73px)] items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <Spinner />
          <p className="text-gray-600 dark:text-slate-400">
            Loading your applications...
          </p>
        </div>
      </div>
    )
  }

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="h-[calc(100vh-73px)] overflow-hidden bg-slate-50 dark:bg-slate-950 p-4">
        <div className="flex gap-3 h-full">
          {boardData.columns.map((column) => (
            <KanbanColumn
              key={column.id}
              column={column}
              onEdit={onEditApplication}
              onAddClick={onAddApplication}
            />
          ))}
        </div>
      </div>
      {isMoving && (
        <div className="pointer-events-none fixed inset-0 bg-black/5 transition-opacity" />
      )}
    </DragDropContext>
  )
}
