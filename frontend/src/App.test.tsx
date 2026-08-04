import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the clinical trial tracker title and profile section', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: /clinical trial tracker/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: /your health profile/i }),
    ).toBeInTheDocument()
  })
})
