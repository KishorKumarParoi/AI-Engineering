import { JobApplication } from '@prisma/client'

export type JobApplicationInsert = Omit<JobApplication, 'id' | 'createdAt' | 'updatedAt'>
export type JobApplicationUpdate = Partial<JobApplicationInsert>
export type ApplicationStatus = 'wishlist' | 'applied' | 'phone_screen' | 'interviewing' | 'offer' | 'rejected' | 'withdrawn'

export type { JobApplication }
