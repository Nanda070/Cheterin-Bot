import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EmbedBuilderPage } from './EmbedBuilder'

describe('EmbedBuilderPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('creates a new embed message', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    const createSpy = vi
      .spyOn(client, 'createEmbedMessage')
      .mockResolvedValue({ message_id: '999', channel_id: '500' })

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Hello' } })
    fireEvent.click(screen.getByText('Отправить'))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith(
        '500',
        expect.objectContaining({ embed: expect.objectContaining({ title: 'Hello' }) }),
      ),
    )
    expect(await screen.findByText(/999/)).toBeInTheDocument()
  })

  it('rejects an empty embed before calling the API', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Заполните хотя бы/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('adds and removes a field', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText('+ Добавить поле'))
    expect(screen.getByPlaceholderText('Название поля')).toBeInTheDocument()

    fireEvent.click(screen.getByText('×'))
    expect(screen.queryByPlaceholderText('Название поля')).not.toBeInTheDocument()
  })

  it('loads an existing message for editing and prefills the form', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchEmbedMessage').mockResolvedValue({
      content: 'existing content',
      embed: {
        title: 'Existing title',
        description: '',
        url: '',
        color: '#5865F2',
        author: { name: '', url: '', icon_url: '' },
        footer: { text: '', icon_url: '' },
        image: { url: '' },
        thumbnail: { url: '' },
        timestamp: null,
        fields: [],
      },
      role_ids: [],
    })

    render(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText('Редактировать существующее'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByPlaceholderText('ID существующего сообщения'), { target: { value: '999' } })
    fireEvent.click(screen.getByText('Загрузить'))

    await waitFor(() => expect(screen.getByLabelText('Title')).toHaveValue('Existing title'))
    expect(screen.getByLabelText('Текст сообщения')).toHaveValue('existing content')
  })

  it('renders the live preview with the current title', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EmbedBuilderPage />)

    fireEvent.change(await screen.findByLabelText('Title'), { target: { value: 'Preview Title' } })
    await waitFor(() => expect(screen.getByText('Preview Title')).toBeInTheDocument())
  })

  it('rejects a spec that exceeds the aggregate 6000-character budget', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'x'.repeat(4096) } })
    fireEvent.change(screen.getByLabelText('Footer'), { target: { value: 'y'.repeat(1905) } })
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Суммарная длина/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('allows saving content-only messages without any embed field', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi
      .spyOn(client, 'createEmbedMessage')
      .mockResolvedValue({ message_id: '999', channel_id: '500' })

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Текст сообщения'), { target: { value: 'Just text' } })
    fireEvent.click(screen.getByText('Отправить'))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith('500', expect.objectContaining({ content: 'Just text' })),
    )
  })

  it('rejects blank content and a blank embed together', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Текст сообщения'), { target: { value: '   ' } })
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Заполните хотя бы/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })
})
