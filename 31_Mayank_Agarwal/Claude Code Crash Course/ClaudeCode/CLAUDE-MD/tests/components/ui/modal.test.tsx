import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Modal } from '@/components/ui/modal'

const baseProps = {
  isOpen: true,
  onClose: vi.fn(),
  title: 'Test Modal',
  children: <p>Modal body</p>,
}

describe('Modal', () => {
  it('renders the title and children when open', () => {
    render(<Modal {...baseProps} />)
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByText('Modal body')).toBeInTheDocument()
  })

  it('renders nothing when isOpen is false', () => {
    render(<Modal {...baseProps} isOpen={false} />)
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument()
    expect(screen.queryByText('Modal body')).not.toBeInTheDocument()
  })

  it('calls onClose when the close button is clicked', () => {
    const onClose = vi.fn()
    render(<Modal {...baseProps} onClose={onClose} />)
    fireEvent.click(screen.getByLabelText('Close modal'))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('calls onClose when Escape is pressed', () => {
    const onClose = vi.fn()
    render(<Modal {...baseProps} onClose={onClose} />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('has the correct dialog role and aria-label', () => {
    render(<Modal {...baseProps} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('locks body scroll while open', () => {
    render(<Modal {...baseProps} />)
    expect(document.body.style.overflow).toBe('hidden')
  })
})
