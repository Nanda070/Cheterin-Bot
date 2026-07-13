import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import * as client from '../api/client'
import { PublicBracketPage } from './PublicBracket'

const baseBracket: client.BracketDetail = {
  id: '1',
  title: 'Летний турнир',
  format: 'single_elim' as const,
  source_event_id: null,
  entries: ['A', 'B'],
  rounds: [[{ slot_a: 'A', slot_b: 'B', winner: 'a' }]],
  share_token: 'my-token',
}

function renderAt(token: string) {
  return render(
    <MemoryRouter initialEntries={[`/bracket/${token}`]}>
      <Routes>
        <Route path="/bracket/:token" element={<PublicBracketPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PublicBracketPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the bracket read-only, with no click handlers', async () => {
    vi.spyOn(client, 'fetchPublicBracket').mockResolvedValue(baseBracket)
    renderAt('my-token')

    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    const slotA = screen.getByText('A')
    expect(slotA.closest('button')).toBeNull()
    expect(screen.queryByText('Поделиться ссылкой')).not.toBeInTheDocument()
    expect(screen.queryByText('Удалить')).not.toBeInTheDocument()
  })

  it('shows an error state for an invalid token', async () => {
    vi.spyOn(client, 'fetchPublicBracket').mockRejectedValue(new Error('not found'))
    renderAt('bad-token')
    expect(await screen.findByText('Сетка не найдена.')).toBeInTheDocument()
  })
})
