import { useMutation, useQueryClient } from '@tanstack/react-query'

import { saveTrial, unsaveTrial } from '../api/client'
import type { MatchScore, TrialLocation } from '../api/types'
import { formatPhase, formatStatus, statusMeaning } from '../utils/format'

interface MatchCardProps {
  match: MatchScore
  userId: string
  isSaved: boolean
}

const MAX_VISIBLE_SITES = 5

function CriteriaList({
  title,
  items,
  variant,
}: {
  title: string
  items: string[]
  variant: 'matched' | 'missing' | 'unknown' | 'handoff'
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

export function MatchCard({ match, userId, isSaved }: MatchCardProps) {
  const queryClient = useQueryClient()
  const scorePercent = Math.round(match.total * 100)
  const confidencePercent = Math.round(match.confidence * 100)
  const locations = match.trial.locations ?? []
  const summary = match.trial.eligibility_criteria_simplified
  const questions = match.questions_for_doctor ?? []

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (isSaved) {
        await unsaveTrial(userId, match.trial.nct_id)
        return
      }
      await saveTrial(userId, match.trial.nct_id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-trials', userId] })
    },
  })

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
      <p className="match-card__status-meaning">
        <span className="match-card__status-meaning-label">What this means:</span>{' '}
        {statusMeaning(match.trial.status)}
      </p>

      <button
        type="button"
        className="button-secondary match-card__save"
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending}
      >
        {isSaved ? 'Remove from saved' : 'Save trial'}
      </button>

      {summary ? (
        <section className="match-card__understanding" aria-label="Trial understanding">
          <h4>What this trial is looking for</h4>
          <p>{summary}</p>
          <p className="match-card__disclaimer">
            Potentially relevant based on your profile — not a recommendation to
            enroll. Discuss with your care team.
          </p>
        </section>
      ) : null}

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
      <CriteriaList
        title="Questions for your doctor"
        items={questions}
        variant="handoff"
      />

      <p className="match-card__rationale">{match.rationale}</p>
      <p className="match-card__confidence">
        {confidencePercent}% eligibility-data confidence
      </p>
    </article>
  )
}
