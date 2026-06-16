import type { JobApplication, ApplicationStatus } from './database'

export interface KanbanColumn {
  id: ApplicationStatus
  title: string
  color: string
  applications: JobApplication[]
}

export interface KanbanBoardData {
  columns: KanbanColumn[]
}
