import { NextRequest, NextResponse } from 'next/server'
import prisma from '@/lib/prisma'
import { validateJobApplicationForm } from '@/lib/validations'
import type { JobApplicationFormData } from '@/types'

export async function GET() {
  try {
    const applications = await prisma.jobApplication.findMany({
      orderBy: [{ status: 'asc' }, { priority: 'asc' }],
    })
    return NextResponse.json({ data: applications, error: null })
  } catch (err) {
    console.error('GET /api/applications:', err)
    return NextResponse.json(
      { data: null, error: 'Failed to fetch applications' },
      { status: 500 },
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const data = (await request.json()) as JobApplicationFormData
    const errors = validateJobApplicationForm(data)

    if (Object.keys(errors).length > 0) {
      return NextResponse.json(
        { data: null, error: JSON.stringify(errors) },
        { status: 400 },
      )
    }

    const maxPriority = await prisma.jobApplication.findFirst({
      where: { status: data.status },
      orderBy: { priority: 'desc' },
      select: { priority: true },
    })

    const newApplication = await prisma.jobApplication.create({
      data: {
        ...data,
        priority: (maxPriority?.priority ?? -1) + 1,
      },
    })

    return NextResponse.json({ data: newApplication, error: null }, { status: 201 })
  } catch (err) {
    console.error('POST /api/applications:', err)
    return NextResponse.json(
      { data: null, error: 'Failed to create application' },
      { status: 500 },
    )
  }
}
