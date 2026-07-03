import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EventsPage } from './Events'

const summary: client.EventSummary = {
  message_id: '900',
  type: 'tournament',
  title: 'Летний турнир',
  status: 'open',
  channel_id: '500',
  count: 5,
}

describe('EventsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists events for the default open filter', async () => {
    const fetchSpy = vi.spyOn(client, 'fetchEvents').mockResolvedValue([summary])

    render(<EventsPage />)

    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    expect(fetchSpy).toHaveBeenCalledWith('open')
  })

  it('reloads with the closed filter when changed', async () => {
    const fetchSpy = vi.spyOn(client, 'fetchEvents').mockResolvedValue([])

    render(<EventsPage />)
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('open'))

    fireEvent.change(screen.getByLabelText('Статус'), { target: { value: 'closed' } })

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('closed'))
  })
})

describe('EventsPage create flow', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('creates a tournament event', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'tourneys' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '200', name: 'Winner', color: '#000000', position: 1 }])
    const createSpy = vi.spyOn(client, 'createEvent').mockResolvedValue({
      message_id: '900',
      type: 'tournament',
      title: 'Летний турнир',
      status: 'open',
      channel_id: '500',
      count: 0,
      description: 'desc',
      role_reward: null,
    })

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Название'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Летний турнир' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'desc' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'tournament', title: 'Летний турнир', channel_id: '500' }),
      ),
    )
  })

  it('creates a poll event with newline-separated options parsed into an array', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'polls' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEvent').mockResolvedValue({
      message_id: '901',
      type: 'poll',
      title: 'Опрос',
      status: 'open',
      channel_id: '500',
      count: 0,
      description: 'desc',
      role_reward: null,
    })

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByText('Опрос'))
    fireEvent.click(screen.getByText('Опрос'))

    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Опрос' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'desc' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Варианты ответа (каждый с новой строки, 2–10)'), {
      target: { value: 'Да\nНет' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith(expect.objectContaining({ type: 'poll', options: ['Да', 'Нет'] })),
    )
  })

  it('toggles between tournament and poll sections', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Формат'))
    expect(screen.queryByLabelText('Варианты ответа (каждый с новой строки, 2–10)')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('Опрос'))

    await waitFor(() => screen.getByLabelText('Варианты ответа (каждый с новой строки, 2–10)'))
    expect(screen.queryByLabelText('Формат')).not.toBeInTheDocument()
  })

  it('shows an error when creation fails', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'tourneys' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'createEvent').mockRejectedValue(new Error('boom'))

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Название'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'T' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'd' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await waitFor(() => screen.getByText('Не удалось создать событие — проверьте поля'))
  })

  it('shows a live preview of the tournament embed as fields are filled in', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'tourneys' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Название'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Летний турнир' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'Описание турнира' } })

    const preview = within(screen.getByTestId('event-embed-preview'))
    expect(preview.getByText('Летний турнир')).toBeInTheDocument()
    expect(preview.getByText('Описание турнира')).toBeInTheDocument()
    expect(preview.getByText('Участники')).toBeInTheDocument()
    expect(preview.getByText('0')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Макс. участников/команд (0 = безлимит)'), { target: { value: '20' } })

    expect(preview.getByText('Лимит')).toBeInTheDocument()
    expect(preview.getByText('0 / 20')).toBeInTheDocument()
  })

  it('shows a live preview of poll options as they are typed', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByText('Опрос'))
    fireEvent.click(screen.getByText('Опрос'))

    fireEvent.change(screen.getByLabelText('Варианты ответа (каждый с новой строки, 2–10)'), {
      target: { value: 'Да\nНет' },
    })

    const preview = within(screen.getByTestId('event-embed-preview'))
    expect(preview.getByText('Да')).toBeInTheDocument()
    expect(preview.getByText('Нет')).toBeInTheDocument()
    expect(preview.getAllByText('░░░░░░░░░░ 0% (0 гол.)')).toHaveLength(2)
  })

  it('preview hides tournament fields when the type is switched to poll', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Формат'))
    const preview = within(screen.getByTestId('event-embed-preview'))
    expect(preview.getByText('Участники')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Опрос'))

    expect(preview.queryByText('Участники')).not.toBeInTheDocument()
  })
})
