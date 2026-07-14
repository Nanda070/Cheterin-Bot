import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { PublicMafiaActionPage } from './PublicMafiaAction'

const baseState: client.MafiaPublicState = {
  game_status: 'active',
  phase: 'night',
  round_number: 1,
  phase_deadline_ts: Math.floor(Date.now() / 1000) + 60,
  your_role: 'doctor',
  your_alive: true,
  action_required: true,
  your_action_submitted: false,
  your_submitted_target: null,
  alive_players: [
    { user_id: '10', display_name: 'Alice' },
    { user_id: '20', display_name: 'Bob' },
  ],
}

function renderAt(token: string) {
  return render(
    <MemoryRouter initialEntries={[`/mafia/${token}`]}>
      <Routes>
        <Route path="/mafia/:token" element={<PublicMafiaActionPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PublicMafiaActionPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows the role, phase and night action controls', async () => {
    vi.spyOn(client, 'fetchPublicMafia').mockResolvedValue(baseState)
    renderAt('my-token')

    expect(await screen.findByText('Доктор')).toBeInTheDocument()
    expect(screen.getByText(/Раунд 1/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Отправить' })).toBeInTheDocument()
  })

  it('shows an error state for an invalid token', async () => {
    vi.spyOn(client, 'fetchPublicMafia').mockRejectedValue(new Error('not found'))
    renderAt('bad-token')
    expect(await screen.findByText('Ссылка недействительна или игра не найдена.')).toBeInTheDocument()
  })

  it('submits a target and shows confirmation', async () => {
    vi.spyOn(client, 'fetchPublicMafia').mockResolvedValue(baseState)
    const submitSpy = vi.spyOn(client, 'submitMafiaAction').mockResolvedValue()
    renderAt('my-token')

    await screen.findByText('Доктор')
    fireEvent.click(screen.getByRole('button', { name: 'Пропустить' }))
    fireEvent.click(await screen.findByRole('option', { name: 'Alice' }))
    fireEvent.click(screen.getByRole('button', { name: 'Отправить' }))

    await screen.findByText('Действие отправлено.')
    expect(submitSpy).toHaveBeenCalledWith('my-token', '10')
  })

  it('hides action controls when no action is required', async () => {
    vi.spyOn(client, 'fetchPublicMafia').mockResolvedValue({
      ...baseState,
      phase: 'day_discussion',
      action_required: false,
    })
    renderAt('my-token')

    await screen.findByText('Доктор')
    expect(screen.queryByRole('button', { name: 'Отправить' })).not.toBeInTheDocument()
    expect(screen.getByText('Сейчас день — обсуждение и голосование проходят в Discord.')).toBeInTheDocument()
  })

  it('shows teammates during the night for mafia players', async () => {
    vi.spyOn(client, 'fetchPublicMafia').mockResolvedValue({
      ...baseState,
      your_role: 'mafia',
      teammates: [{ user_id: '99', display_name: 'Charlie' }],
      mafia_votes: [],
    })
    renderAt('my-token')

    expect(await screen.findByText('Команда мафии')).toBeInTheDocument()
    expect(screen.getByText('Charlie')).toBeInTheDocument()
  })
})
