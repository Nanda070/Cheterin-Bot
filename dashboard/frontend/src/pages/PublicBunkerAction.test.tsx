import { fireEvent, screen } from '@testing-library/react'
import { Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { PublicBunkerActionPage } from './PublicBunkerAction'

const baseState: client.BunkerPublicState = {
  game_status: 'active',
  phase: 'discussion',
  round_number: 1,
  phase_deadline_ts: Math.floor(Date.now() / 1000) + 60,
  bunker_capacity: 2,
  catastrophe_name: 'Ядерная война',
  catastrophe_description: 'Ядерный удар накрыл города.',
  bunker_conditions_name: 'Тесное убежище',
  bunker_conditions_description: 'Места мало, запасов на месяц.',
  your_alive: true,
  your_character: {
    profession: { name: 'Пожарный', category: 'МЧС', experience_level: 'Эксперт', has_ability: true },
    age: { key: 'adult', label: 'Взрослый (35-59 лет)' },
    gender: 'Мужской',
    special_abilities: [
      { name: 'Джокер', category: 'Защита', effect: 'эффект 1', used: false },
      { name: 'Сейф', category: 'Защита', effect: 'эффект 2', used: false },
    ],
  },
  your_revealed_fields: [],
  action_required: false,
  your_vote_submitted: false,
  your_submitted_target: null,
  alive_players: [
    { user_id: '10', display_name: 'Alice' },
    { user_id: '20', display_name: 'Bob' },
  ],
  roster: [
    { user_id: '10', display_name: 'Alice', alive: true, character: {}, revealed_fields: [] },
    {
      user_id: '20',
      display_name: 'Bob',
      alive: true,
      character: { profession: { name: 'Врач', category: 'Медицина', experience_level: 'Опытный', has_ability: true } },
      revealed_fields: ['profession'],
    },
  ],
}

function renderAt(token: string) {
  return renderWithLanguage(
    <Routes>
      <Route path="/bunker/:token" element={<PublicBunkerActionPage />} />
    </Routes>,
    { initialEntries: [`/bunker/${token}`] },
  )
}

describe('PublicBunkerActionPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows the character card and phase info', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockResolvedValue(baseState)
    renderAt('my-token')

    expect(await screen.findByText('Пожарный (Эксперт, есть способность) — МЧС')).toBeInTheDocument()
    expect(screen.getByText(/Раунд 1/)).toBeInTheDocument()
    expect(screen.getByText(/Ядерная война/)).toBeInTheDocument()
  })

  it('shows an error state for an invalid token', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockRejectedValue(new Error('not found'))
    renderAt('bad-token')
    expect(await screen.findByText('Ссылка недействительна или игра не найдена.')).toBeInTheDocument()
  })

  it('reveals a field and calls the API', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockResolvedValue(baseState)
    const revealSpy = vi.spyOn(client, 'revealBunkerFields').mockResolvedValue()
    renderAt('my-token')

    await screen.findByText('Пожарный (Эксперт, есть способность) — МЧС')
    fireEvent.click(screen.getAllByRole('button', { name: 'Раскрыть' })[0])

    expect(revealSpy).toHaveBeenCalledWith('my-token', ['profession'])
  })

  it('shows the roster with revealed fields for other players', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockResolvedValue(baseState)
    renderAt('my-token')

    expect(await screen.findByText('Игроки (2/2)')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText(/Профессия: Врач/)).toBeInTheDocument()
  })

  it('opens the ability form and submits a usage announcement', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockResolvedValue(baseState)
    const announceSpy = vi.spyOn(client, 'announceBunkerAbility').mockResolvedValue()
    renderAt('my-token')

    await screen.findByText('Джокер')
    fireEvent.click(screen.getAllByRole('button', { name: 'Использовать' })[0])
    fireEvent.click(screen.getByRole('button', { name: 'Без цели' }))
    fireEvent.click(await screen.findByRole('option', { name: 'Bob' }))
    fireEvent.change(screen.getByPlaceholderText('Как применить (необязательно)'), {
      target: { value: 'меняю профессию' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Стоп игра! Заявить' }))

    expect(announceSpy).toHaveBeenCalledWith('my-token', 1, '20', 'меняю профессию')
  })

  it('shows the vote card and submits a vote during the vote phase', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockResolvedValue({
      ...baseState,
      phase: 'vote',
      action_required: true,
      vote_tally: [{ target: '20', target_display: 'Bob', count: 1 }],
    })
    const voteSpy = vi.spyOn(client, 'submitBunkerVote').mockResolvedValue()
    renderAt('my-token')

    expect(await screen.findByText('Голосование за исключение')).toBeInTheDocument()
    expect(screen.getByText('Текущие голоса')).toBeInTheDocument()
    expect(screen.getByText('Bob: 1')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Пропустить' }))
    fireEvent.click(await screen.findByRole('option', { name: 'Bob' }))
    fireEvent.click(screen.getByRole('button', { name: 'Отправить' }))

    expect(voteSpy).toHaveBeenCalledWith('my-token', '20')
  })

  it('hides the vote card outside the vote phase', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockResolvedValue(baseState)
    renderAt('my-token')

    await screen.findByText('Пожарный (Эксперт, есть способность) — МЧС')
    expect(screen.queryByText('Голосование за исключение')).not.toBeInTheDocument()
  })

  it('switches UI language when API returns language', async () => {
    vi.spyOn(client, 'fetchPublicBunker').mockResolvedValue({ ...baseState, language: 'en' })
    renderAt('my-token')

    expect(await screen.findByText('Bunker game')).toBeInTheDocument()
    expect(screen.getByText('Your card')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Reveal' }).length).toBeGreaterThan(0)
  })
})
