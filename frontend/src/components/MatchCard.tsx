import type { MatchScore, TrialLocation } from '../api/types'
import { formatPhase, formatStatus } from '../utils/format'

interface MatchCardProps {
  match: MatchScore
}

const MAX_VISIBLE_SITES = 5

function CriteriaList({
  title,
  items,
  variant,
}: {
  title: string
  items: string[]
  variant: 'matched' | 'missing' | 'unknown'
}) {
  if (items.length === 0) {
    return null
  }

  return (
    <section className={`criteria criteria--${variant}`} aria-label={title}>
      <h4>{title}</h4>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  )
}

function formatSite(location: TrialLocation): string {
  const parts = [location.facility, location.city, location.country].filter(
    (part): part is string => Boolean(part && part.trim()),
  )
  return parts.join(', ')
}

function SiteList({ locations }: { locations: TrialLocation[] }) {
  if (locations.length === 0) {
    return (
      <p className="match-card__sites match-card__sites--empty">
        Sites: not listed on ClinicalTrials.gov yet
      </p>
    )
  }

  const visible = locations.slice(0, MAX_VISIBLE_SITES)
  const remaining = locations.length - visible.length

  return (
    <section className="match-card__sites" aria-label="Trial sites">
      <h4>Sites</h4>
      <ul>
        {visible.map((location, index) => (
          <li key={`${location.city ?? 'site'}-${index}`}>{formatSite(location)}</li>
        ))}
      </ul>
      {remaining > 0 ? (
        <p className="match-card__sites-more">+{remaining} more sites</p>
      ) : null}
    </section>
  )
}

export function MatchCard({ match }: MatchCardProps) {
  const scorePercent = Math.round(match.total * 100)
  const confidencePercent = Math.round(match.confidence * 100)
  const locations = match.trial.locations ?? []

  return (
    <article className="match-card">
      <header className="match-card__header">
        <h3>{match.trial.title}</h3>
        <span className="match-card__score">{scorePercent}% compatible</span>
      </header>

      <p className="match-card__meta">
        {match.trial.nct_id} · {formatPhase(match.trial.phase)} ·{' '}
        {formatStatus(match.trial.status)}
        {match.nearest_site_miles != null
          ? ` · ~${Math.round(match.nearest_site_miles)} mi to nearest site`
          : ''}
      </p>

      <SiteList locations={locations} />

      <CriteriaList
        title="Matched"
        items={match.matched_criteria}
        variant="matched"
      />
      <CriteriaList
        title="Not met"
        items={match.missing_criteria}
        variant="missing"
      />
      <CriteriaList
        title="Unable to verify"
        items={match.unknown_criteria}
        variant="unknown"
      />

      <p className="match-card__rationale">{match.rationale}</p>
      <p className="match-card__confidence">
        {confidencePercent}% eligibility-data confidence
      </p>
    </article>
  )
}
