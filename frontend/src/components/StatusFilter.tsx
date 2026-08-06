import type { TrialStatus } from '../api/types'
import { formatStatus } from '../utils/format'

/** Patient Mode default: join-now intent (excludes Enrolling by invitation). */
export const PATIENT_DEFAULT_STATUSES: TrialStatus[] = [
  'RECRUITING',
  'NOT_YET_RECRUITING',
]

export const PATIENT_FILTER_STATUSES: TrialStatus[] = [
  'RECRUITING',
  'NOT_YET_RECRUITING',
  'ACTIVE_NOT_RECRUITING',
  'ENROLLING_BY_INVITATION',
  'COMPLETED',
  'TERMINATED',
  'WITHDRAWN',
  'SUSPENDED',
]

type ShowMode = 'join_now' | 'include_completed'

interface StatusFilterProps {
  selected: TrialStatus[]
  onChange: (statuses: TrialStatus[]) => void
}

function toggleStatus(
  selected: TrialStatus[],
  status: TrialStatus,
): TrialStatus[] {
  if (selected.includes(status)) {
    const next = selected.filter((item) => item !== status)
    return next.length > 0 ? next : [...PATIENT_DEFAULT_STATUSES]
  }
  return [...selected, status]
}

export function StatusFilter({ selected, onChange }: StatusFilterProps) {
  const mode: ShowMode =
    selected.includes('COMPLETED') &&
    PATIENT_DEFAULT_STATUSES.every((status) => selected.includes(status))
      ? 'include_completed'
      : 'join_now'

  return (
    <fieldset className="status-filter">
      <legend>Filter by status</legend>
      <p className="status-filter__hint">
        Labels match ClinicalTrials.gov. Default shows trials you may join now.
      </p>

      <div className="status-filter__modes" role="radiogroup" aria-label="Show me">
        <label className="status-filter__mode">
          <input
            type="radio"
            name="status-show-mode"
            checked={mode === 'join_now'}
            onChange={() => onChange([...PATIENT_DEFAULT_STATUSES])}
          />
          Trials I may join now
        </label>
        <label className="status-filter__mode">
          <input
            type="radio"
            name="status-show-mode"
            checked={mode === 'include_completed'}
            onChange={() =>
              onChange([
                ...PATIENT_DEFAULT_STATUSES,
                'COMPLETED',
                'ACTIVE_NOT_RECRUITING',
              ])
            }
          />
          All research including completed studies
        </label>
      </div>

      <div className="status-filter__checks">
        {PATIENT_FILTER_STATUSES.map((status) => (
          <label key={status} className="status-filter__check">
            <input
              type="checkbox"
              checked={selected.includes(status)}
              onChange={() => onChange(toggleStatus(selected, status))}
            />
            {formatStatus(status)}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
