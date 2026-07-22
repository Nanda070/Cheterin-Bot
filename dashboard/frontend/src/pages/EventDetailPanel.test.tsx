import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EventDetailPanel } from './EventDetailPanel'

const tournamentDetail: client.EventDetail = {
  message_id: '900',
  type: 'tournament',
  title: 'Летний турнир',
  status: 'open',
  channel_id: '500',
  count: 1,
  description: 'desc',
  role_reward: null,
  mode: 'solo',
  max_limit: 0,
  team_size: 5,
  participants: [{ user_id: '20', ign: 'PlayerOne' }],
}

const pollDetail: client.EventDetail = {
  message_id: '901',
  type: 'poll',
  title: 'Опрос дня',
  status: 'open',
  channel_id: '500',
  count: 2,
  description: 'desc',
  role_reward: null,
  multi_select: false,
  options: [
    { label: 'Да', votes: 2, percent: 100 },
    { label: 'Нет', votes: 0, percent: 0 },
  ],
}

describe('EventDetailPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders tournament participants', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)

    renderWithLanguage(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={() => {}} />)

    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    expect(screen.getByText('PlayerOne')).toBeInTheDocument()
  })

  it('renders poll vote percentages', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(pollDetail)

    renderWithLanguage(<EventDetailPanel messageId="901" onClose={() => {}} onChanged={() => {}} />)

    expect(await screen.findByText('Опрос дня')).toBeInTheDocument()
    expect(screen.getByText('Да')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('closes an event', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)
    const closeSpy = vi.spyOn(client, 'closeEvent').mockResolvedValue(undefined)
    const onChanged = vi.fn()

    renderWithLanguage(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={onChanged} />)

    await waitFor(() => screen.getByText('Закрыть'))
    fireEvent.click(screen.getByText('Закрыть'))

    await waitFor(() => expect(closeSpy).toHaveBeenCalledWith('900'))
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })

  it('deletes an event after confirmation', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)
    const deleteSpy = vi.spyOn(client, 'deleteEvent').mockResolvedValue(undefined)
    const onChanged = vi.fn()

    renderWithLanguage(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={onChanged} />)

    await waitFor(() => screen.getByText('Удалить'))
    fireEvent.click(screen.getByText('Удалить'))
    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить событие' }))

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('900'))
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })

  it('sends a notification to participants', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)
    const notifySpy = vi.spyOn(client, 'notifyEventParticipants').mockResolvedValue({ success: 1, failed: 0 })

    renderWithLanguage(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={() => {}} />)

    await waitFor(() => screen.getByText('Рассылка'))
    fireEvent.click(screen.getByText('Рассылка'))

    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Текст сообщения'), { target: { value: 'Привет!' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Отправить' }))

    await waitFor(() => expect(notifySpy).toHaveBeenCalledWith('900', 'Привет!'))
  })
})
