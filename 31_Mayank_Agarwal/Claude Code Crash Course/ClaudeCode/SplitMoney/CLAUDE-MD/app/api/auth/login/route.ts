import { NextRequest, NextResponse } from 'next/server'
import { TEST_USER, SESSION_COOKIE, SESSION_TOKEN } from '@/lib/auth'

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    if (email !== TEST_USER.email || password !== TEST_USER.password) {
      return NextResponse.json(
        { data: null, error: 'Invalid email or password' },
        { status: 401 },
      )
    }

    const response = NextResponse.json({ data: { name: TEST_USER.name }, error: null })
    response.cookies.set(SESSION_COOKIE, SESSION_TOKEN, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
    })

    return response
  } catch {
    return NextResponse.json({ data: null, error: 'Login failed' }, { status: 500 })
  }
}
