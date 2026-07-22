import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { GiveawaysPage } from './Giveaways'

const emptyOverview: client.GiveawayOverview = { active: [], history: [] }

function mockBaseFetches(overview: client.GiveawayOverview = emptyOverview) {
  vi.spyOn(client, 'fetchGiveawayOverview').mockResolvedValue(overview)
  vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
}

describe('GiveawaysPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the page with no active giveaways', async () => {
    mockBaseFetches()
    renderWithLanguage(<GiveawaysPage />)

    expect(await screen.findByText('Активных розыгрышей нет.')).toBeInTheDocument()
    expect(screen.getByText('Истории пока нет.')).toBeInTheDocument()
  })

  it('lists an active giveaway and ends it', async () => {
    mockBaseFetches({
      active: [
        {
          id: '1',
          initiator_id: '10',
          initiator_display: 'mod',
          prize: 'Discord Nitro',
          winners_count: 1,
          duration_str: '10m',
          target_ts: 1234567890,
          status: 'active',
          entrants: [{ id: '100', display: 'Alice' }],
          winners: [],
          channel_id: '500',
          created_at: '2026-01-01T00:00:00Z',
          closed_at: null,
        },
      ],
      history: [],
    })
    const endSpy = vi.spyOn(client, 'endGiveaway').mockResolvedValue()

    renderWithLanguage(<GiveawaysPage />)

    expect(await screen.findByText(/Discord Nitro/)).toBeInTheDocument()
    expect(screen.getByText(/Alice/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Завершить' }))
    await waitFor(() => expect(endSpy).toHaveBeenCalledWith('1'))
  })

  it('lists a finished giveaway with winners and allows reroll', async () => {
    mockBaseFetches({
      active: [],
      history: [
        {
          id: '2',
          initiator_id: '10',
          initiator_display: 'mod',
          prize: 'Steam-ключ',
          winners_count: 1,
          duration_str: '1h',
          target_ts: 1234567890,
          status: 'finished',
          entrants: [{ id: '100', display: 'Alice' }, { id: '200', display: 'Bob' }],
          winners: [{ id: '100', display: 'Alice' }],
          channel_id: '500',
          created_at: '2026-01-01T00:00:00Z',
          closed_at: '2026-01-01T01:00:00Z',
        },
      ],
    })
    const rerollSpy = vi.spyOn(client, 'rerollGiveaway').mockResolvedValue({ winners: ['200'] })

    renderWithLanguage(<GiveawaysPage />)

    expect(await screen.findByText(/Steam-ключ/)).toBeInTheDocument()
    expect(screen.getByText('🏆 Alice')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Реролл' }))
    await waitFor(() => expect(rerollSpy).toHaveBeenCalledWith('2'))
  })

  it('creates a new giveaway via the modal', async () => {
    mockBaseFetches()
    const createSpy = vi.spyOn(client, 'createGiveaway').mockResolvedValue({
      id: '3',
      initiator_id: '10',
      initiator_display: 'mod',
      prize: 'Приз',
      winners_count: 1,
      duration_str: '10m',
      target_ts: 1234567890,
      status: 'active',
      entrants: [],
      winners: [],
      channel_id: '500',
      created_at: '2026-01-01T00:00:00Z',
      closed_at: null,
    })

    renderWithLanguage(<GiveawaysPage />)
    await screen.findByText('Активных розыгрышей нет.')

    fireEvent.click(screen.getByRole('button', { name: /Новый розыгрыш/ }))

    fireEvent.click(screen.getByRole('button', { name: 'Канал публикации' }))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))

    fireEvent.change(screen.getByLabelText('Приз'), { target: { value: 'Discord Nitro' } })
    fireEvent.change(screen.getByLabelText('Длительность'), { target: { value: '10m' } })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith({
        channel_id: '500',
        prize: 'Discord Nitro',
        duration_str: '10m',
        winners_count: 1,
      }),
    )
  })
})
