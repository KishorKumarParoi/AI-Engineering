'use client'

import React, { useState } from 'react'
import type { JobApplication, JobApplicationFormData } from '@/types'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Select } from './ui/select'
import { validateJobApplicationForm } from '@/lib/validations'
import { KANBAN_COLUMNS } from '@/lib/constants'

interface JobApplicationFormProps {
  initialData?: JobApplication
  onSubmit: (data: JobApplicationFormData) => Promise<void>
  isLoading?: boolean
}

export function JobApplicationForm({
  initialData,
  onSubmit,
  isLoading = false,
}: JobApplicationFormProps) {
  const [formData, setFormData] = useState<JobApplicationFormData>({
    companyName: initialData?.companyName ?? '',
    roleTitle: initialData?.roleTitle ?? '',
    status: (initialData?.status as any) ?? 'applied',
    jobUrl: initialData?.jobUrl ?? '',
    location: initialData?.location ?? '',
    salaryRange: initialData?.salaryRange ?? '',
    appliedDate: initialData?.appliedDate ?? '',
    notes: initialData?.notes ?? '',
    contactName: initialData?.contactName ?? '',
    contactEmail: initialData?.contactEmail ?? '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    setErrors((prev) => ({ ...prev, [name]: '' }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const validationErrors = validateJobApplicationForm(formData)

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    try {
      await onSubmit(formData)
    } catch (err) {
      console.error('Form submission error:', err)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Company Name *"
        name="companyName"
        value={formData.companyName}
        onChange={handleChange}
        error={errors.companyName}
        placeholder="e.g. Google"
      />

      <Input
        label="Role Title *"
        name="roleTitle"
        value={formData.roleTitle}
        onChange={handleChange}
        error={errors.roleTitle}
        placeholder="e.g. Senior Engineer"
      />

      <Select
        label="Status *"
        name="status"
        value={formData.status}
        onChange={handleChange}
        error={errors.status}
        options={KANBAN_COLUMNS.map((col) => ({
          value: col.id,
          label: col.title,
        }))}
      />

      <Input
        label="Job URL"
        name="jobUrl"
        type="url"
        value={formData.jobUrl}
        onChange={handleChange}
        error={errors.jobUrl}
        placeholder="https://..."
      />

      <Input
        label="Location"
        name="location"
        value={formData.location}
        onChange={handleChange}
        placeholder="e.g. San Francisco, CA"
      />

      <Input
        label="Salary Range"
        name="salaryRange"
        value={formData.salaryRange}
        onChange={handleChange}
        placeholder="e.g. $120k-$150k"
      />

      <Input
        label="Applied Date"
        name="appliedDate"
        type="date"
        value={formData.appliedDate}
        onChange={handleChange}
      />

      <Input
        label="Contact Name"
        name="contactName"
        value={formData.contactName}
        onChange={handleChange}
        placeholder="Recruiter or hiring manager"
      />

      <Input
        label="Contact Email"
        name="contactEmail"
        type="email"
        value={formData.contactEmail}
        onChange={handleChange}
        error={errors.contactEmail}
        placeholder="email@example.com"
      />

      <Textarea
        label="Notes"
        name="notes"
        value={formData.notes}
        onChange={handleChange}
        placeholder="Any additional notes..."
        rows={3}
      />

      <Button type="submit" variant="primary" isLoading={isLoading} className="w-full">
        {initialData ? 'Update Application' : 'Add Application'}
      </Button>
    </form>
  )
}
