import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MatchResults } from './MatchResults'
import { sampleMatch } from '../test/fixtures'

describe('MatchResults', () => {
  it('shows a loading state', () => {
    render(<MatchResults matches={[]} isLoading={true} error={null} />)

    expect(screen.getByText(/loading trial matches/i)).toBeInTheDocument()
  })

  it('shows an error message', () => {
    render(
      <MatchResults
        matches={[]}
        isLoading={false}
        error={new Error('Profile not found')}
      />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('Profile not found')
  })

  it('shows an empty state when there are no matches', () => {
    render(<MatchResults matches={[]} isLoading={false} error={null} />)

    expect(
      screen.getByText(/no matching trials found/i),
    ).toBeInTheDocument()
  })

  it('renders match cards for each result', () => {
    render(
      <MatchResults
        matches={[sampleMatch]}
        isLoading={false}
        error={null}
      />,
    )

    expect(
      screen.getByRole('heading', {
        name: /phase 2 study of trastuzumab deruxtecan/i,
      }),
    ).toBeInTheDocument()
  })
})
