import { NextRequest, NextResponse } from 'next/server'
import { SESSION_COOKIE, SESSION_TOKEN } from '@/lib/auth'

export function middleware(request: NextRequest) {
  const session = request.cookies.get(SESSION_COOKIE)
  const isAuthenticated = session?.value === SESSION_TOKEN
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/api/auth')) return NextResponse.next()

  if (pathname.startsWith('/api/')) {
    if (!isAuthenticated) {
      return NextResponse.json({ data: null, error: 'Unauthorized' }, { status: 401 })
    }
    return NextResponse.next()
  }

  if (!isAuthenticated && pathname !== '/login') {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (isAuthenticated && pathname === '/login') {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
