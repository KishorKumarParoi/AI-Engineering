import React from 'react'
import type { ApplicationStatus } from '@/types'
import { STATUS_BADGE_COLORS } from '@/lib/constants'

interface BadgeProps {
  status: ApplicationStatus
  className?: string
}

export function Badge({ status, className }: BadgeProps) {
  return (
    <span
      className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${
        STATUS_BADGE_COLORS[status]
      } ${className || ''}`}
    >
      {status.replace('_', ' ')}
    </span>
  )
}
