import { NextRequest, NextResponse } from 'next/server'
import prisma from '@/lib/prisma'
import type { JobApplicationFormData } from '@/types'

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const application = await prisma.jobApplication.findUnique({
      where: { id: params.id },
    })

    if (!application) {
      return NextResponse.json(
        { data: null, error: 'Application not found' },
        { status: 404 },
      )
    }

    return NextResponse.json({ data: application, error: null })
  } catch (err) {
    console.error('GET /api/applications/[id]:', err)
    return NextResponse.json(
      { data: null, error: 'Failed to fetch application' },
      { status: 500 },
    )
  }
}

export async function PATCH(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const data = (await request.json()) as Partial<JobApplicationFormData>

    const updated = await prisma.jobApplication.update({
      where: { id: params.id },
      data,
    })

    return NextResponse.json({ data: updated, error: null })
  } catch (err) {
    console.error('PATCH /api/applications/[id]:', err)
    return NextResponse.json(
      { data: null, error: 'Failed to update application' },
      { status: 500 },
    )
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    await prisma.jobApplication.delete({
      where: { id: params.id },
    })

    return NextResponse.json({ data: null, error: null })
  } catch (err) {
    console.error('DELETE /api/applications/[id]:', err)
    return NextResponse.json(
      { data: null, error: 'Failed to delete application' },
      { status: 500 },
    )
  }
}
