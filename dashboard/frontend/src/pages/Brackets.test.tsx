import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import * as client from '../api/client'
import { BracketsPage } from './Brackets'

function renderPage() {
  return render(
    <MemoryRouter>
      <BracketsPage />
    </MemoryRouter>,
  )
}

describe('BracketsPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lists existing brackets', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([
      { id: '1', title: 'Летний турнир', source_event_id: null, entry_count: 8, created_at: '2026-07-04T00:00:00Z' },
    ])
    renderPage()
    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
  })

  it('shows an empty state when there are no brackets', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([])
    renderPage()
    expect(await screen.findByText('Сеток пока нет.')).toBeInTheDocument()
  })

  it('creates a bracket manually from typed names', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([])
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createBracket').mockResolvedValue({
      id: '1',
      title: 'Manual',
      source_event_id: null,
      entries: ['X', 'Y'],
      rounds: [],
      share_token: null,
    })

    renderPage()
    fireEvent.click(await screen.findByText('Создать сетку'))
    fireEvent.click(screen.getByText('Вручную'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Manual' } })
    fireEvent.change(screen.getByLabelText('Имена (по одному на строку)'), { target: { value: 'X\nY' } })
    fireEvent.click(screen.getByText('Далее'))
    fireEvent.click(screen.getByText('Сгенерировать'))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('Manual', ['X', 'Y'], null))
  })

  it('loads entries from a selected event and allows reordering', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([])
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([
      { message_id: '900', type: 'tournament', title: 'Кубок', status: 'closed', channel_id: '1', count: 2 },
    ])
    vi.spyOn(client, 'fetchEventEntries').mockResolvedValue(['Alpha', 'Beta'])
    const createSpy = vi.spyOn(client, 'createBracket').mockResolvedValue({
      id: '1',
      title: 'From Event',
      source_event_id: '900',
      entries: ['Beta', 'Alpha'],
      rounds: [],
      share_token: null,
    })

    renderPage()
    fireEvent.click(await screen.findByText('Создать сетку'))
    fireEvent.change(await screen.findByLabelText('Событие'), { target: { value: '900' } })
    await screen.findByText('Загружено участников: 2')
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'From Event' } })
    fireEvent.click(screen.getByText('Далее'))

    // The seed step (reached after "Далее") is what actually renders each entry's name.
    await screen.findByText('Alpha')

    // Move Beta above Alpha using the down-arrow on the first row.
    fireEvent.click(screen.getAllByLabelText('Переместить вниз')[0])

    fireEvent.click(screen.getByText('Сгенерировать'))
    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('From Event', ['Beta', 'Alpha'], '900'))
  })
})
