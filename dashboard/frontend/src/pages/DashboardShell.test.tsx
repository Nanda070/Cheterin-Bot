import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import { DashboardShell } from './DashboardShell'

describe('DashboardShell', () => {
  it('renders the "Cheterin" header title as a link to the home page', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
    })

    render(
      <MemoryRouter initialEntries={['/members']}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<div>Home Page Marker</div>} />
            <Route path="/members" element={<DashboardShell />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    const title = await screen.findByText('Cheterin')
    expect(title.closest('a')).toHaveAttribute('href', '/')

    fireEvent.click(title)
    expect(await screen.findByText('Home Page Marker')).toBeInTheDocument()
  })

  it('renders the user avatar and username at the top of the sidebar', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
    })

    render(
      <MemoryRouter initialEntries={['/members']}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<div>Home Page Marker</div>} />
            <Route path="/members" element={<DashboardShell />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    const usernameNodes = await screen.findAllByText('tester')
    expect(usernameNodes.length).toBeGreaterThanOrEqual(2)
  })

  it('lists nav entries for Welcome and Auto Roles', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
    })

    render(
      <MemoryRouter initialEntries={['/members']}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<div>Home Page Marker</div>} />
            <Route path="/members" element={<DashboardShell />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Приветствие и прощание')).toBeInTheDocument()
    expect(screen.getByText('Авто-роли')).toBeInTheDocument()
  })
})
