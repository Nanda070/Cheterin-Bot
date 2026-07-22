import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { WelcomePage } from './Welcome'

describe('WelcomePage', () => {
  it('redirects to server entry', () => {
    render(
      <MemoryRouter initialEntries={['/welcome']}>
        <Routes>
          <Route path="/welcome" element={<WelcomePage />} />
          <Route path="/server-entry" element={<div>Server entry</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Server entry')).toBeInTheDocument()
  })
})
