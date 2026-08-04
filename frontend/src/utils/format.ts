const PHASE_LABELS: Record<string, string> = {
  PHASE_1: 'Phase 1',
  PHASE_2: 'Phase 2',
  PHASE_3: 'Phase 3',
  PHASE_4: 'Phase 4',
  NOT_APPLICABLE: 'N/A',
}

const STATUS_LABELS: Record<string, string> = {
  RECRUITING: 'Recruiting',
  NOT_YET_RECRUITING: 'Not yet recruiting',
  ACTIVE_NOT_RECRUITING: 'Active, not recruiting',
  ENROLLING_BY_INVITATION: 'Enrolling by invitation',
  SUSPENDED: 'Suspended',
  COMPLETED: 'Completed',
  TERMINATED: 'Terminated',
  WITHDRAWN: 'Withdrawn',
  AVAILABLE: 'Available',
  NO_LONGER_AVAILABLE: 'No longer available',
  APPROVED_FOR_MARKETING: 'Approved for marketing',
  WITHHELD: 'Withheld',
  UNKNOWN: 'Unknown',
}

export function formatPhase(phase: string): string {
  return PHASE_LABELS[phase] ?? phase
}

export function formatStatus(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll('_', ' ').toLowerCase()
}
