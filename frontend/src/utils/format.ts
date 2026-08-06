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

const STATUS_MEANINGS: Record<string, string> = {
  RECRUITING: 'This trial is currently looking for participants.',
  NOT_YET_RECRUITING:
    'The study is registered but is not accepting participants yet.',
  ACTIVE_NOT_RECRUITING:
    'The study is ongoing but is not currently enrolling new participants.',
  ENROLLING_BY_INVITATION:
    'Participation is limited to people invited by the study team.',
  SUSPENDED: 'Enrollment or study activity is temporarily paused.',
  COMPLETED:
    'The study has finished. Results may help explain why a treatment became standard care — this is not an open enrollment opportunity.',
  TERMINATED: 'The study was stopped early and is not enrolling.',
  WITHDRAWN: 'The study was withdrawn before enrolling participants.',
  AVAILABLE: 'Expanded access to the intervention may be available.',
  NO_LONGER_AVAILABLE: 'Expanded access is no longer available.',
  APPROVED_FOR_MARKETING: 'The intervention has been approved for marketing.',
  WITHHELD: 'Status details are withheld on ClinicalTrials.gov.',
  UNKNOWN: 'Status could not be mapped from ClinicalTrials.gov.',
}

export function formatPhase(phase: string): string {
  return PHASE_LABELS[phase] ?? phase
}

export function formatStatus(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll('_', ' ').toLowerCase()
}

export function statusMeaning(status: string): string {
  return (
    STATUS_MEANINGS[status] ??
    'See ClinicalTrials.gov for status details.'
  )
}
