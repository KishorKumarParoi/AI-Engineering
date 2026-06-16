import { NextResponse } from 'next/server'
import { SESSION_COOKIE } from '@/lib/auth'

export async function POST() {
  const response = NextResponse.json({ data: null, error: null })
  response.cookies.delete(SESSION_COOKIE)
  return response
}
