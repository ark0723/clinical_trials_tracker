import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { Dashboard } from './Dashboard'
import { sampleMatch, sampleProfile } from '../test/fixtures'
import { renderWithQueryClient } from '../test/test-utils'

const USER_ID_KEY = 'clinical_tracker_user_id'

describe('Dashboard', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('shows the profile form when no saved user exists', () => {
    renderWithQueryClient(<Dashboard />)

    expect(
      screen.getByRole('heading', { name: /your health profile/i }),
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/^age$/i)).toBeInTheDocument()
  })

  it('creates a profile and displays match results', async () => {
    const user = userEvent.setup()

    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const url = String(input)

      if (url.includes('/api/users/profile') && init?.method === 'POST') {
        return new Response(JSON.stringify(sampleProfile), { status: 201 })
      }

      if (url.includes('/api/matches/user-123')) {
        return new Response(JSON.stringify({ matches: [sampleMatch] }), {
          status: 200,
        })
      }

      return new Response('Not found', { status: 404 })
    })

    renderWithQueryClient(<Dashboard />)

    await user.clear(screen.getByLabelText(/^age$/i))
    await user.type(screen.getByLabelText(/^age$/i), '45')
    await user.selectOptions(screen.getByLabelText(/cancer stage/i), 'III')
    await user.click(screen.getByRole('button', { name: /save profile/i }))

    await waitFor(() => {
      expect(localStorage.getItem(USER_ID_KEY)).toBe('user-123')
    })

    expect(
      await screen.findByRole('heading', { name: /recommended trials/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', {
        name: /phase 2 study of trastuzumab deruxtecan/i,
      }),
    ).toBeInTheDocument()
  })
})
