import { fireEvent, screen, waitFor } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackCasesPage } from './FeedbackCases'

describe('FeedbackCasesPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists cases filtered to pending by default', async () => {
    vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([
      {
        case_id: 'PR-0001',
        category_key: 'players',
        category_title: 'Жалоба на участника',
        submitter_id: '50',
        submitter_display: 'submitter',
        status: 'pending',
        created_at: '2026-07-03T00:00:00+00:00',
      },
    ])

    renderWithLanguage(<FeedbackCasesPage />)

    await waitFor(() => expect(client.fetchFeedbackCases).toHaveBeenCalledWith('pending'))
    expect(
      await screen.findByText((_, element) => element?.textContent === 'submitter · pending'),
    ).toBeInTheDocument()
  })

  it('reloads with the selected status filter', async () => {
    const fetchSpy = vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([])

    renderWithLanguage(<FeedbackCasesPage />)

    await waitFor(() => screen.getByLabelText('Статус'))
    fireEvent.click(screen.getByLabelText('Статус'))
    fireEvent.click(screen.getByRole('option', { name: 'Принято' }))

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('approved'))
  })

  it('shows empty state when there are no cases', async () => {
    vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([])

    renderWithLanguage(<FeedbackCasesPage />)

    expect(await screen.findByText('Обращений нет.')).toBeInTheDocument()
  })
})
