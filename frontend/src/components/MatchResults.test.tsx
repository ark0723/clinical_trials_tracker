import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MatchResults } from './MatchResults'
import { sampleMatch } from '../test/fixtures'
import { renderWithQueryClient } from '../test/test-utils'

const emptySaved = new Set<string>()

describe('MatchResults', () => {
  it('shows a loading state', () => {
    render(
      <MatchResults
        matches={[]}
        isLoading={true}
        error={null}
        userId="user-123"
        savedNctIds={emptySaved}
      />,
    )

    expect(screen.getByText(/loading trial matches/i)).toBeInTheDocument()
  })

  it('shows an error message', () => {
    render(
      <MatchResults
        matches={[]}
        isLoading={false}
        error={new Error('Profile not found')}
        userId="user-123"
        savedNctIds={emptySaved}
      />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('Profile not found')
  })

  it('shows an empty state when there are no matches', () => {
    render(
      <MatchResults
        matches={[]}
        isLoading={false}
        error={null}
        userId="user-123"
        savedNctIds={emptySaved}
      />,
    )

    expect(
      screen.getByText(/no matching trials found/i),
    ).toBeInTheDocument()
  })

  it('renders match cards for each result', () => {
    renderWithQueryClient(
      <MatchResults
        matches={[sampleMatch]}
        isLoading={false}
        error={null}
        userId="user-123"
        savedNctIds={emptySaved}
      />,
    )

    expect(
      screen.getByRole('heading', {
        name: /phase 2 study of trastuzumab deruxtecan/i,
      }),
    ).toBeInTheDocument()
  })
})
