'use client'

import React from 'react'
import type { KanbanColumn as KanbanColumnType, JobApplication } from '@/types'
import { JobCard } from './job-card'
import { Button } from './ui/button'
import { EmptyState } from './ui/empty-state'
import { Draggable, Droppable } from '@hello-pangea/dnd'

interface KanbanColumnProps {
  column: KanbanColumnType
  onEdit: (application: JobApplication) => void
  onAddClick: (status: string) => void
}

export const KanbanColumn = React.memo(function KanbanColumn({
  column,
  onEdit,
  onAddClick,
}: KanbanColumnProps) {
  return (
    <div className={`flex flex-col rounded-lg ${column.color} w-56 flex-shrink-0 shadow-sm`}>
      <div className="border-b border-gray-200 dark:border-slate-500 px-3 py-2">
        <div className="mb-2 flex items-center justify-between gap-2">
          <h2 className="font-semibold text-sm text-gray-900 dark:text-white truncate">
            {column.title}
          </h2>
          <span className="rounded-full bg-gray-300 dark:bg-slate-500 px-2 py-0.5 text-xs font-medium text-gray-800 dark:text-white flex-shrink-0">
            {column.applications.length}
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full border border-dashed border-gray-300 dark:border-slate-500 hover:border-blue-400 dark:hover:border-blue-400 text-gray-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-blue-50/50 dark:hover:bg-blue-900/40"
          onClick={() => onAddClick(column.id)}
        >
          + Add
        </Button>
      </div>

      <Droppable droppableId={column.id}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`flex-1 space-y-2 overflow-y-auto p-3 transition-colors ${
              snapshot.isDraggingOver
                ? 'bg-blue-50 dark:bg-blue-950/30'
                : ''
            }`}
          >
            {column.applications.length === 0 && !snapshot.isDraggingOver && (
              <EmptyState title="No applications" />
            )}
            {column.applications.map((app, index) => (
              <Draggable key={app.id} draggableId={app.id} index={index}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    className={`transition-all ${
                      snapshot.isDragging ? 'opacity-50 shadow-lg' : ''
                    }`}
                  >
                    <JobCard application={app} onEdit={onEdit} />
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </div>
  )
})
