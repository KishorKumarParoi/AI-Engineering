// @vitest-environment node
import { describe, it, expect } from 'vitest'
import { NextRequest } from 'next/server'
import { POST } from '@/app/api/auth/login/route'
import { SESSION_COOKIE, TEST_USER } from '@/lib/auth'

function makeLoginRequest(body: object): NextRequest {
  return new NextRequest('http://localhost/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('POST /api/auth/login', () => {
  it('returns 200 and sets a session cookie on valid credentials', async () => {
    const res = await POST(makeLoginRequest({ email: TEST_USER.email, password: TEST_USER.password }))

    expect(res.status).toBe(200)

    const body = await res.json()
    expect(body.error).toBeNull()
    expect(body.data.name).toBe(TEST_USER.name)

    const cookie = res.cookies.get(SESSION_COOKIE)
    expect(cookie).toBeDefined()
    expect(cookie!.value).toBeTruthy()
  })

  it('returns 401 for a wrong password', async () => {
    const res = await POST(makeLoginRequest({ email: TEST_USER.email, password: 'wrong-password' }))

    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error).toBe('Invalid email or password')
    expect(body.data).toBeNull()
  })

  it('returns 401 for a wrong email', async () => {
    const res = await POST(makeLoginRequest({ email: 'nobody@example.com', password: TEST_USER.password }))

    expect(res.status).toBe(401)
    const body = await res.json()
    expect(body.error).toBe('Invalid email or password')
  })

  it('does not set a cookie on failed login', async () => {
    const res = await POST(makeLoginRequest({ email: 'x@x.com', password: 'wrong' }))
    expect(res.cookies.get(SESSION_COOKIE)).toBeUndefined()
  })
})
