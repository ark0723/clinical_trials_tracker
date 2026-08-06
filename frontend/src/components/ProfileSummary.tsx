import type { UserProfile } from '../api/types'
import { CURRENT_TREATMENT_OPTIONS } from '../api/types'

interface ProfileSummaryProps {
  profile: UserProfile
  onEdit: () => void
}

function treatmentLabel(value: UserProfile['current_treatment']): string {
  const option = CURRENT_TREATMENT_OPTIONS.find((item) => item.value === value)
  if (!option) {
    return value
  }
  // Prefer short clinical name in the summary card (e.g. "Trastuzumab").
  return option.label.split(' (')[0] ?? option.label
}

function subtypeLabel(profile: UserProfile): string {
  if (profile.biomarkers.includes('HER2-positive')) {
    return 'HER2+'
  }
  return profile.biomarkers.join(', ') || 'Not specified'
}

export function ProfileSummary({ profile, onEdit }: ProfileSummaryProps) {
  const rows: { label: string; value: string }[] = [
    { label: 'Age', value: String(profile.age) },
    { label: 'Cancer Type', value: 'Breast Cancer' },
    { label: 'Subtype', value: subtypeLabel(profile) },
    { label: 'Stage', value: profile.stage },
    {
      label: 'ECOG',
      value: profile.ecog === null || profile.ecog === undefined
        ? 'Not specified'
        : String(profile.ecog),
    },
    { label: 'Current Treatment', value: treatmentLabel(profile.current_treatment) },
    {
      label: 'Travel Distance',
      value: `${profile.max_travel_distance_miles} miles`,
    },
  ]

  return (
    <div className="profile-summary" aria-label="Your profile">
      <dl className="profile-summary__grid">
        {rows.map((row) => (
          <div key={row.label} className="profile-summary__row">
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </div>
        ))}
      </dl>
      <button type="button" className="button-secondary" onClick={onEdit}>
        Edit
      </button>
    </div>
  )
}
