import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackPage } from './Feedback'

describe('FeedbackPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows cases by default and switches to categories tab', async () => {
    vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([])
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderWithLanguage(<FeedbackPage />)

    await waitFor(() => screen.getByRole('button', { name: 'Обращения' }))
    expect(screen.getByText('Обращений нет.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Категории' }))
    await waitFor(() => screen.getByText('Создать категорию'))
  })
})
