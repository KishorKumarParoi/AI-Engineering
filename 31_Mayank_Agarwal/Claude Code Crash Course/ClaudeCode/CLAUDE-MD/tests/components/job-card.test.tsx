import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { JobCard } from '@/components/job-card'
import type { JobApplication } from '@/types'

vi.mock('@/lib/format-date', () => ({
  formatApplicationDate: vi.fn(() => 'Apr 15, 2024'),
  getRelativeDays: vi.fn(() => '5 days ago'),
}))

const mockApp: JobApplication = {
  id: 'app-1',
  companyName: 'Acme Corp',
  roleTitle: 'Senior Engineer',
  status: 'applied',
  jobUrl: 'https://acme.com/jobs',
  location: 'San Francisco, CA',
  salaryRange: '$150k–$180k',
  appliedDate: '2024-04-10',
  notes: 'Great opportunity at Acme',
  contactName: 'Jane Doe',
  contactEmail: 'jane@acme.com',
  priority: 0,
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
}

describe('JobCard', () => {
  const onEdit = vi.fn()

  beforeEach(() => onEdit.mockClear())

  it('renders company name and role title', () => {
    render(<JobCard application={mockApp} onEdit={onEdit} />)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
  })

  it('renders the relative applied date', () => {
    render(<JobCard application={mockApp} onEdit={onEdit} />)
    expect(screen.getByText(/Applied.*5 days ago/)).toBeInTheDocument()
  })

  it('renders location when provided', () => {
    render(<JobCard application={mockApp} onEdit={onEdit} />)
    expect(screen.getByText(/San Francisco, CA/)).toBeInTheDocument()
  })

  it('renders salary range when provided', () => {
    render(<JobCard application={mockApp} onEdit={onEdit} />)
    expect(screen.getByText(/\$150k/)).toBeInTheDocument()
  })

  it('renders notes when provided', () => {
    render(<JobCard application={mockApp} onEdit={onEdit} />)
    expect(screen.getByText(/Great opportunity at Acme/)).toBeInTheDocument()
  })

  it('calls onEdit when the card is clicked', () => {
    render(<JobCard application={mockApp} onEdit={onEdit} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onEdit).toHaveBeenCalledOnce()
    expect(onEdit).toHaveBeenCalledWith(mockApp)
  })

  it('calls onEdit when Enter is pressed on the card', () => {
    render(<JobCard application={mockApp} onEdit={onEdit} />)
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' })
    expect(onEdit).toHaveBeenCalledWith(mockApp)
  })

  it('does not render location when absent', () => {
    render(<JobCard application={{ ...mockApp, location: null }} onEdit={onEdit} />)
    expect(screen.queryByText(/San Francisco/)).not.toBeInTheDocument()
  })

  it('does not render notes section when absent', () => {
    render(<JobCard application={{ ...mockApp, notes: null }} onEdit={onEdit} />)
    expect(screen.queryByText(/Great opportunity/)).not.toBeInTheDocument()
  })
})
