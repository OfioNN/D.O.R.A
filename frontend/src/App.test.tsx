import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import App from './App.tsx'

it('pokazuje nazwę asystenta', () => {
  render(<App />)
  expect(screen.getByRole('heading', { name: 'DORA' })).toBeInTheDocument()
})
