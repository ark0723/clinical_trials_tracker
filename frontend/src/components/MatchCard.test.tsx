import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MatchCard } from './MatchCard'
import { sampleMatch } from '../test/fixtures'
import { renderWithQueryClient } from '../test/test-utils'

describe('MatchCard', () => {
  it('renders trial title, NCT ID, and match score', () => {
    renderWithQueryClient(
      <MatchCard match={sampleMatch} userId="user-123" isSaved={false} />,
    )

    expect(
      screen.getByRole('heading', {
        name: /phase 2 study of trastuzumab deruxtecan/i,
      }),
    ).toBeInTheDocument()
    expect(screen.getByText(/NCT01234567/i)).toBeInTheDocument()
    expect(screen.getByText(/85% compatible/i)).toBeInTheDocument()
  })

  it('renders matched, missing, and unknown criteria', () => {
    renderWithQueryClient(
      <MatchCard match={sampleMatch} userId="user-123" isSaved={false} />,
    )

    expect(screen.getByText('HER2-positive biomarker')).toBeInTheDocument()
    expect(screen.getByText('Required prior treatment')).toBeInTheDocument()
    expect(screen.getByText('Age: unable to verify')).toBeInTheDocument()
  })

  it('renders plain-English understanding and doctor questions', () => {
    renderWithQueryClient(
      <MatchCard match={sampleMatch} userId="user-123" isSaved={false} />,
    )

    expect(
      screen.getByRole('heading', { name: /what this trial is looking for/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Adults with HER2-positive breast cancer/i),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: /questions for your doctor/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/What is my current ECOG performance status/i),
    ).toBeInTheDocument()
  })

  it('renders plain-English rationale and confidence', () => {
    renderWithQueryClient(
      <MatchCard match={sampleMatch} userId="user-123" isSaved={false} />,
    )

    expect(
      screen.getByText(/This trial targets HER2-positive breast cancer/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/78% eligibility-data confidence/i),
    ).toBeInTheDocument()
  })

  it('renders trial sites and save control', () => {
    renderWithQueryClient(
      <MatchCard match={sampleMatch} userId="user-123" isSaved={false} />,
    )

    expect(screen.getByRole('heading', { name: /^sites$/i })).toBeInTheDocument()
    expect(
      screen.getByText(/Dana-Farber Cancer Institute, Boston/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /save trial/i })).toBeInTheDocument()
  })
})
