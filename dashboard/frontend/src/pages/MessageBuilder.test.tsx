import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { MessageBuilderPage } from './MessageBuilder'

describe('MessageBuilderPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows Reaction Roles content by default and switches to the Эмбеды tab', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])

    render(<MessageBuilderPage />)

    await waitFor(() => screen.getByRole('button', { name: 'Reaction Roles' }))
    expect(screen.getByText('Пока ничего не настроено.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Эмбеды' }))
    await waitFor(() => screen.getByLabelText(/^Title/))
  })
})
