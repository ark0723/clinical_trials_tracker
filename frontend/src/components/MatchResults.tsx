import type { MatchScore } from '../api/types'
import { MatchCard } from './MatchCard'

interface MatchResultsProps {
  matches: MatchScore[]
  isLoading: boolean
  error: Error | null
}

export function MatchResults({ matches, isLoading, error }: MatchResultsProps) {
  if (isLoading) {
    return <p className="status-message">Loading trial matches…</p>
  }

  if (error) {
    return (
      <p className="status-message status-message--error" role="alert">
        {error.message}
      </p>
    )
  }

  if (matches.length === 0) {
    return (
      <p className="status-message">
        No matching trials found for your profile. Try updating your profile or
        check back after the next trial sync.
      </p>
    )
  }

  return (
    <div className="match-results">
      {matches.map((match) => (
        <MatchCard key={match.trial.nct_id} match={match} />
      ))}
    </div>
  )
}
