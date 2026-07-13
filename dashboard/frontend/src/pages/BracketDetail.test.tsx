import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import * as client from '../api/client'
import { BracketDetailPage } from './BracketDetail'

function renderAt(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/brackets/${id}`]}>
      <Routes>
        <Route path="/brackets/:id" element={<BracketDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

const baseBracket: client.BracketDetail = {
  id: '1',
  title: 'Летний турнир',
  format: 'single_elim' as const,
  source_event_id: null,
  entries: ['A', 'B', 'C', 'D'],
  rounds: [
    [
      { slot_a: 'A', slot_b: 'B', winner: null },
      { slot_a: 'C', slot_b: 'D', winner: null },
    ],
    [{ slot_a: null, slot_b: null, winner: null }],
  ],
  share_token: null,
}

describe('BracketDetailPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the bracket title and matches', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    renderAt('1')
    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('D')).toBeInTheDocument()
  })

  it('clicking a slot sets the winner and refreshes the bracket', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    const winnerSpy = vi.spyOn(client, 'setBracketMatchWinner').mockResolvedValue({
      ...baseBracket,
      rounds: [
        [
          { slot_a: 'A', slot_b: 'B', winner: 'a' },
          { slot_a: 'C', slot_b: 'D', winner: null },
        ],
        [{ slot_a: 'A', slot_b: null, winner: null }],
      ],
    })

    renderAt('1')
    fireEvent.click(await screen.findByText('A'))
    await waitFor(() => expect(winnerSpy).toHaveBeenCalledWith('1', 0, 0, 'a', 'W'))
  })

  it('does not render a click handler for a match with a pending slot', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    renderAt('1')
    await screen.findByText('Летний турнир')
    // The final round has both slots null (pending) — there is nothing clickable there yet.
    const pendingSlots = screen.getAllByText('—')
    expect(pendingSlots).toHaveLength(2)
    for (const slot of pendingSlots) {
      expect(slot.closest('button')).toBeNull()
    }
  })

  it('enables sharing and shows the public link', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    vi.spyOn(client, 'enableBracketShare').mockResolvedValue('my-token')

    renderAt('1')
    fireEvent.click(await screen.findByText('Поделиться ссылкой'))
    expect(await screen.findByText(/my-token/)).toBeInTheDocument()
  })

  it('deletes the bracket after confirmation', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    const deleteSpy = vi.spyOn(client, 'deleteBracket').mockResolvedValue()

    renderAt('1')
    fireEvent.click(await screen.findByText('Удалить'))
    fireEvent.click(screen.getByText('Подтвердить'))
    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('1'))
  })
})
