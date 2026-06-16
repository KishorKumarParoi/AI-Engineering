'use client'

import { useState } from 'react'
import { Modal } from './ui/modal'
import { JobApplicationForm } from './job-application-form'
import { useJobApplications } from '@/lib/context'
import type { JobApplicationFormData } from '@/types'

interface AddApplicationModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AddApplicationModal({ isOpen, onClose }: AddApplicationModalProps) {
  const { addApplication } = useJobApplications()
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (data: JobApplicationFormData) => {
    setIsLoading(true)
    try {
      await addApplication(data)
      onClose()
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Job Application">
      <JobApplicationForm onSubmit={handleSubmit} isLoading={isLoading} />
    </Modal>
  )
}
