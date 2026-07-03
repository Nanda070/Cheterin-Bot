import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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
