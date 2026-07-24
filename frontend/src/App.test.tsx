import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the clinical trial tracker title', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: /clinical trial tracker/i }),
    ).toBeInTheDocument()
  })
})
