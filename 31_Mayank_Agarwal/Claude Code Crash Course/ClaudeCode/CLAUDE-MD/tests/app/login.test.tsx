import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import LoginPage from '@/app/login/page'

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

describe('LoginPage', () => {
  const mockPush = vi.fn()
  const mockRefresh = vi.fn()

  beforeEach(() => {
    vi.mocked(useRouter).mockReturnValue({ push: mockPush, refresh: mockRefresh } as any)
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    mockPush.mockClear()
    mockRefresh.mockClear()
  })

  it('renders email and password fields', () => {
    render(<LoginPage />)
    expect(screen.getByPlaceholderText('admin@test.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
  })

  it('renders the sign-in button', () => {
    render(<LoginPage />)
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows the test credentials hint', () => {
    render(<LoginPage />)
    expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    expect(screen.getByText('password123')).toBeInTheDocument()
  })

  it('displays an error message on failed login', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      json: () => Promise.resolve({ data: null, error: 'Invalid email or password' }),
    } as Response)

    render(<LoginPage />)
    fireEvent.change(screen.getByPlaceholderText('admin@test.com'), {
      target: { value: 'wrong@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'wrongpass' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await screen.findByText('Invalid email or password')
    expect(screen.getByText('Invalid email or password')).toBeInTheDocument()
  })

  it('redirects to / on successful login', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      json: () => Promise.resolve({ data: { name: 'Mayank' }, error: null }),
    } as Response)

    render(<LoginPage />)
    fireEvent.change(screen.getByPlaceholderText('admin@test.com'), {
      target: { value: 'admin@test.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/'))
    expect(mockRefresh).toHaveBeenCalled()
  })

  it('posts to /api/auth/login with the entered credentials', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      json: () => Promise.resolve({ data: { name: 'Mayank' }, error: null }),
    } as Response)

    render(<LoginPage />)
    fireEvent.change(screen.getByPlaceholderText('admin@test.com'), {
      target: { value: 'admin@test.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(fetch).toHaveBeenCalled())
    const [url, options] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe('/api/auth/login')
    expect(options?.method).toBe('POST')
    const body = JSON.parse(options?.body as string)
    expect(body).toEqual({ email: 'admin@test.com', password: 'password123' })
  })
})
