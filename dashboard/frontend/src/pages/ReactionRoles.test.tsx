import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { ReactionRolesPage } from './ReactionRoles'

describe('ReactionRolesPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lists existing reaction roles with resolved channel/role names', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([
      { message_id: '999', channel_id: '500', pairs: [{ emoji: '📖', role_id: '7' }] },
    ])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])

    render(
      <MemoryRouter>
        <ReactionRolesPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('general')).toBeInTheDocument())
    expect(screen.getByText('VIP')).toBeInTheDocument()
  })

  it('opens the create form and submits a new reaction role', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createReactionRole').mockResolvedValue({
      message_id: '999',
      channel_id: '500',
      pairs: [{ emoji: '📖', role_id: '7' }],
    })

    render(
      <MemoryRouter>
        <ReactionRolesPage />
      </MemoryRouter>,
    )

    await waitFor(() => screen.getByText('Создать reaction role'))
    fireEvent.click(screen.getByText('Создать reaction role'))

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Message ID'), { target: { value: '999' } })
    fireEvent.change(screen.getByPlaceholderText('Эмодзи (вставьте unicode или выберите ниже)'), {
      target: { value: '📖' },
    })
    fireEvent.click(screen.getByLabelText('Роль для этой пары'))
    fireEvent.click(await screen.findByRole('option', { name: 'VIP' }))
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('500', '999', [{ emoji: '📖', role_id: '7' }]))
  })

  it('rejects submit with duplicate emoji before calling the API', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([
      { id: '7', name: 'VIP', color: '#5865f2', position: 5 },
      { id: '8', name: 'Other', color: '#000000', position: 5 },
    ])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createReactionRole')

    render(
      <MemoryRouter>
        <ReactionRolesPage />
      </MemoryRouter>,
    )

    await waitFor(() => screen.getByText('Создать reaction role'))
    fireEvent.click(screen.getByText('Создать reaction role'))
    await waitFor(() => screen.getByLabelText('Канал'))

    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Message ID'), { target: { value: '999' } })
    fireEvent.change(screen.getByPlaceholderText('Эмодзи (вставьте unicode или выберите ниже)'), {
      target: { value: '📖' },
    })
    fireEvent.click(screen.getByLabelText('Роль для этой пары'))
    fireEvent.click(await screen.findByRole('option', { name: 'VIP' }))

    fireEvent.click(screen.getByText('+ Добавить пару'))
    const emojiInputs = screen.getAllByPlaceholderText('Эмодзи (вставьте unicode или выберите ниже)')
    fireEvent.change(emojiInputs[1], { target: { value: '📖' } })
    const roleSelects = screen.getAllByLabelText('Роль для этой пары')
    fireEvent.click(roleSelects[1])
    fireEvent.click(await screen.findByRole('option', { name: 'Other' }))

    fireEvent.click(screen.getByText('Сохранить'))

    expect(await screen.findByText(/повторяющ/i)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })
})
