'use client'

import React from 'react'
import type { JobApplication } from '@/types'
import { Badge } from './ui/badge'
import { formatApplicationDate, getRelativeDays } from '@/lib/format-date'

interface JobCardProps {
  application: JobApplication
  onEdit: (application: JobApplication) => void
}

export const JobCard = React.memo(function JobCard({ application, onEdit }: JobCardProps) {
  return (
    <div
      className="group cursor-grab active:cursor-grabbing rounded-md border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 shadow-sm dark:shadow-slate-900 transition-all hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:focus-visible:ring-blue-400"
      onClick={() => onEdit(application)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onEdit(application)
        }
      }}
    >
      <div className="mb-1.5 flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm text-gray-900 dark:text-white group-hover:text-blue-700 dark:group-hover:text-blue-400 transition-colors truncate">
            {application.companyName}
          </h3>
          <p className="text-xs text-gray-600 dark:text-slate-400 truncate">
            {application.roleTitle}
          </p>
        </div>
      </div>

      <Badge status={application.status as any} className="mb-1.5 block w-fit" />

      <div className="space-y-0.5 text-xs text-gray-500 dark:text-slate-500">
        {application.appliedDate && (
          <p>Applied {getRelativeDays(application.appliedDate)}</p>
        )}
        {application.location && (
          <p className="text-gray-600 dark:text-slate-400">📍 {application.location}</p>
        )}
        {application.salaryRange && (
          <p className="text-gray-600 dark:text-slate-400 font-medium">
            💰 {application.salaryRange}
          </p>
        )}
      </div>

      {application.notes && (
        <div className="mt-2 rounded-md bg-gray-50 dark:bg-slate-700/50 p-2 text-xs text-gray-600 dark:text-slate-400 border-l-2 border-blue-200 dark:border-blue-800">
          <p className="line-clamp-2 italic">{application.notes}</p>
        </div>
      )}
    </div>
  )
})
