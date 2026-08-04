import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ProfileForm } from './ProfileForm'

describe('ProfileForm', () => {
  it('renders profile input fields including clinical selects', () => {
    render(<ProfileForm onSubmit={vi.fn()} />)

    expect(screen.getByLabelText(/^age$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/cancer stage/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/HER2-positive/i)).toBeInTheDocument()
    expect(
      screen.getByLabelText(/current or most recent treatment/i),
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/ZIP \/ postal code/i)).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /^ECOG performance status$/i })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /^Brain metastases$/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/max travel distance/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email notifications/i)).toBeInTheDocument()
  })

  it('exposes definitions for ECOG and brain metastases', () => {
    render(<ProfileForm onSubmit={vi.fn()} />)

    expect(
      screen.getByRole('button', { name: /what does ecog performance status mean/i }),
    ).toHaveAttribute('title', expect.stringContaining('0–4 score'))
    expect(
      screen.getByRole('button', { name: /what does brain metastases mean/i }),
    ).toHaveAttribute('title', expect.stringContaining('spread to the brain'))
  })

  it('submits profile data when the form is valid', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(<ProfileForm onSubmit={onSubmit} />)

    await user.clear(screen.getByLabelText(/^age$/i))
    await user.type(screen.getByLabelText(/^age$/i), '45')
    await user.selectOptions(screen.getByLabelText(/cancer stage/i), 'III')
    await user.selectOptions(
      screen.getByLabelText(/current or most recent treatment/i),
      'trastuzumab',
    )
    await user.type(screen.getByLabelText(/ZIP \/ postal code/i), '10001')
    await user.selectOptions(
      screen.getByRole('combobox', { name: /^ECOG performance status$/i }),
      '1',
    )
    await user.selectOptions(
      screen.getByRole('combobox', { name: /^Brain metastases$/i }),
      'no',
    )
    await user.click(screen.getByRole('button', { name: /save profile/i }))

    expect(onSubmit).toHaveBeenCalledWith({
      age: 45,
      cancer_type: 'HER2_POSITIVE_BREAST',
      stage: 'III',
      biomarkers: ['HER2-positive'],
      current_treatment: 'trastuzumab',
      postal_code: '10001',
      ecog: 1,
      brain_metastasis: 'no',
      max_travel_distance_miles: 50,
      notification_channels: ['email'],
    })
  })
})
