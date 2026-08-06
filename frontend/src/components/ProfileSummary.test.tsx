import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ProfileSummary } from './ProfileSummary'
import { sampleProfile } from '../test/fixtures'
import { renderWithQueryClient } from '../test/test-utils'

describe('ProfileSummary', () => {
  it('renders saved profile fields for the dashboard', () => {
    renderWithQueryClient(
      <ProfileSummary profile={sampleProfile} onEdit={() => undefined} />,
    )

    expect(screen.getByText('Age')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
    expect(screen.getByText('Breast Cancer')).toBeInTheDocument()
    expect(screen.getByText('HER2+')).toBeInTheDocument()
    expect(screen.getByText('III')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('Trastuzumab')).toBeInTheDocument()
    expect(screen.getByText('100 miles')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^edit$/i })).toBeInTheDocument()
  })
})
