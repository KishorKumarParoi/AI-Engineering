'use client'

import { useState } from 'react'
import type { JobApplication } from '@/types'
import { Modal } from './ui/modal'
import { Button } from './ui/button'
import { JobApplicationForm } from './job-application-form'
import { useJobApplications } from '@/lib/context'
import type { JobApplicationFormData } from '@/types'

interface EditApplicationModalProps {
  isOpen: boolean
  onClose: () => void
  application: JobApplication | null
}

export function EditApplicationModal({ isOpen, onClose, application }: EditApplicationModalProps) {
  const { updateApplication, deleteApplication } = useJobApplications()
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (data: JobApplicationFormData) => {
    if (!application) return
    setIsLoading(true)
    try {
      await updateApplication(application.id, data)
      onClose()
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!application) return
    if (!window.confirm('Are you sure? This cannot be undone.')) return

    setIsLoading(true)
    try {
      await deleteApplication(application.id)
      onClose()
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Job Application">
      {application && (
        <div className="space-y-4">
          <JobApplicationForm
            initialData={application}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
          <Button
            variant="danger"
            className="w-full"
            onClick={handleDelete}
            isLoading={isLoading}
          >
            Delete
          </Button>
        </div>
      )}
    </Modal>
  )
}
