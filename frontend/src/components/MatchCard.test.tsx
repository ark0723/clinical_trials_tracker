import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MatchCard } from './MatchCard'
import { sampleMatch } from '../test/fixtures'

describe('MatchCard', () => {
  it('renders trial title, NCT ID, and match score', () => {
    render(<MatchCard match={sampleMatch} />)

    expect(
      screen.getByRole('heading', {
        name: /phase 2 study of trastuzumab deruxtecan/i,
      }),
    ).toBeInTheDocument()
    expect(screen.getByText(/NCT01234567/i)).toBeInTheDocument()
    expect(screen.getByText(/85% compatible/i)).toBeInTheDocument()
  })

  it('renders matched, missing, and unknown criteria', () => {
    render(<MatchCard match={sampleMatch} />)

    expect(screen.getByText('HER2-positive biomarker')).toBeInTheDocument()
    expect(screen.getByText('Required prior treatment')).toBeInTheDocument()
    expect(screen.getByText('Age: unable to verify')).toBeInTheDocument()
  })

  it('renders plain-English rationale and confidence', () => {
    render(<MatchCard match={sampleMatch} />)

    expect(
      screen.getByText(/This trial targets HER2-positive breast cancer/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/78% eligibility-data confidence/i),
    ).toBeInTheDocument()
  })

  it('renders trial sites', () => {
    render(<MatchCard match={sampleMatch} />)

    expect(screen.getByRole('heading', { name: /^sites$/i })).toBeInTheDocument()
    expect(
      screen.getByText(/Dana-Farber Cancer Institute, Boston/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Memorial Sloan Kettering, New York/i),
    ).toBeInTheDocument()
  })
})
