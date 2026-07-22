import { fireEvent, screen, waitFor } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { MafiaPage } from './Mafia'

const emptySettings: client.MafiaSettings = {
  enabled: false,
  default_min_players: 5,
  default_max_players: 20,
  default_night_timer_sec: 60,
  default_day_discussion_timer_sec: 120,
  default_day_vote_timer_sec: 60,
  log_channel_id: '',
}

function mockBaseFetches(settings: client.MafiaSettings = emptySettings) {
  vi.spyOn(client, 'fetchMafiaSettings').mockResolvedValue(settings)
  vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
}

describe('MafiaPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the module toggle and tabs', async () => {
    mockBaseFetches()
    renderWithLanguage(<MafiaPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Настройки' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Активные игры' })).toBeInTheDocument()
  })

  it('toggles enabled and saves settings', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateMafiaSettings').mockResolvedValue({ ...emptySettings, enabled: true })

    renderWithLanguage(<MafiaPage />)
    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true })))
    expect(await screen.findByText('Сохранено')).toBeInTheDocument()
  })

  it('updates a timer field before saving', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateMafiaSettings').mockResolvedValue(emptySettings)
    renderWithLanguage(<MafiaPage />)

    const input = await screen.findByLabelText(/^Ночь/)
    fireEvent.change(input, { target: { value: '90' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ default_night_timer_sec: 90 })),
    )
  })

  it('lists active games', async () => {
    mockBaseFetches()
    vi.spyOn(client, 'fetchMafiaGames').mockResolvedValue([
      {
        id: 1,
        channel_id: '500',
        channel_name: 'general',
        status: 'active',
        phase: 'night',
        round_number: 2,
        player_count: 8,
        alive_count: 6,
        created_at: '2026-01-01T00:00:00Z',
      },
    ])

    renderWithLanguage(<MafiaPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Активные игры' }))

    expect(await screen.findByText('Игра #1 · general')).toBeInTheDocument()
    expect(screen.getByText(/раунд 2/)).toBeInTheDocument()
  })
})
