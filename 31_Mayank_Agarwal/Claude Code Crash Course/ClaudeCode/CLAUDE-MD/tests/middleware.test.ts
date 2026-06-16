// @vitest-environment node
import { describe, it, expect } from 'vitest'
import { NextRequest } from 'next/server'
import { middleware } from '@/middleware'
import { SESSION_COOKIE, SESSION_TOKEN } from '@/lib/auth'

function makeRequest(path: string, authenticated = false): NextRequest {
  const headers: Record<string, string> = {}
  if (authenticated) {
    headers['cookie'] = `${SESSION_COOKIE}=${SESSION_TOKEN}`
  }
  return new NextRequest(`http://localhost${path}`, { headers })
}

describe('middleware', () => {
  describe('unauthenticated requests', () => {
    it('redirects page requests to /login', () => {
      const res = middleware(makeRequest('/'))
      expect(res.status).toBe(307)
      expect(res.headers.get('location')).toContain('/login')
    })

    it('redirects nested page requests to /login', () => {
      const res = middleware(makeRequest('/some/page'))
      expect(res.status).toBe(307)
      expect(res.headers.get('location')).toContain('/login')
    })

    it('returns 401 JSON for API requests', async () => {
      const res = middleware(makeRequest('/api/applications'))
      expect(res.status).toBe(401)
      const body = await res.json()
      expect(body.error).toBe('Unauthorized')
      expect(body.data).toBeNull()
    })

    it('allows /api/auth/* without a session', () => {
      const res = middleware(makeRequest('/api/auth/login'))
      expect(res.status).not.toBe(307)
      expect(res.status).not.toBe(401)
    })

    it('allows access to /login without a session', () => {
      const res = middleware(makeRequest('/login'))
      expect(res.status).not.toBe(307)
    })
  })

  describe('authenticated requests', () => {
    it('allows access to the root page', () => {
      const res = middleware(makeRequest('/', true))
      expect(res.status).not.toBe(307)
      expect(res.status).not.toBe(401)
    })

    it('allows API requests', () => {
      const res = middleware(makeRequest('/api/applications', true))
      expect(res.status).not.toBe(307)
      expect(res.status).not.toBe(401)
    })

    it('redirects away from /login back to /', () => {
      const res = middleware(makeRequest('/login', true))
      expect(res.status).toBe(307)
      expect(res.headers.get('location')).toBe('http://localhost/')
    })
  })
})
