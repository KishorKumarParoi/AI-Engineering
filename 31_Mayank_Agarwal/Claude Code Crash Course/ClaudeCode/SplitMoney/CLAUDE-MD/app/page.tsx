'use client'

import { useState } from 'react'
import { Navbar } from '@/components/navbar'
import { KanbanBoard } from '@/components/kanban-board'
import { AddApplicationModal } from '@/components/add-application-modal'
import { EditApplicationModal } from '@/components/edit-application-modal'
import type { JobApplication } from '@/types'

export default function Home() {
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [selectedApplication, setSelectedApplication] = useState<JobApplication | null>(null)

  const handleEditApplication = (app: JobApplication) => {
    setSelectedApplication(app)
    setEditModalOpen(true)
  }

  const handleAddApplication = () => {
    setAddModalOpen(true)
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <KanbanBoard
        onEditApplication={handleEditApplication}
        onAddApplication={handleAddApplication}
      />
      <AddApplicationModal isOpen={addModalOpen} onClose={() => setAddModalOpen(false)} />
      <EditApplicationModal
        isOpen={editModalOpen}
        onClose={() => {
          setEditModalOpen(false)
          setSelectedApplication(null)
        }}
        application={selectedApplication}
      />
    </div>
  )
}
