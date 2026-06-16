import type { ApplicationStatus } from './database'

export interface JobApplicationFormData {
  companyName: string
  roleTitle: string
  status: ApplicationStatus
  jobUrl: string
  location: string
  salaryRange: string
  appliedDate: string
  notes: string
  contactName: string
  contactEmail: string
}
