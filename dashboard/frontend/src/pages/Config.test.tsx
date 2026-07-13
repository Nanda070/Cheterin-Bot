import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { ConfigPage } from './Config'

const emptyConfig: client.BotConfig = {
  LOG_CHANNEL_ID: '',
  SPAM_EXCEPTION_CHANNELS: [],
  TEMPBAN_CHANNEL_ID: '',
  SPAM_LOG_CHANNEL_ID: '',
  SPAM_LOG_ROLE_ID: '',
  WELCOME_CHANNEL_ID: '',
  INVITE_LOG_CHANNEL_ID: '',
  ANNOUNCEMENTS_CHANNEL_ID: '',
  RULES_CHANNEL_ID: '',
  ROLES_CHANNEL_ID: '',
  SEARCH_PLAYERS_CHANNEL_ID: '',
  CTD_ROLE_ID: '',
  CTD_CHANNEL_ID: '',
  BUTTON_CREATE_ALLOWED_ROLES: [],
  BUTTON_WEBHOOK_URL: '',
  SERVER_INVITE_LINK: '',
  VOICE_LOBBY_CHANNEL_ID: '',
  VOICE_PANEL_CHANNEL_ID: '',
  VOICE_LOG_CHANNEL_ID: '',
  VOICE_PANEL_THUMB_URL: '',
  SUPPLY_ROLE_ID: '',
  SUPPLY_VOICE_CHANNEL_ID: '',
  SUPPLY_LOG_CHANNEL_ID: '',
  SUPPLY_REMINDER_MINUTES: '',
}

describe('ConfigPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders all config sections', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(emptyConfig)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<ConfigPage />)

    expect(await screen.findByText('Модерация и спам')).toBeInTheDocument()
    expect(screen.getByText('Приветствия и онбординг')).toBeInTheDocument()
    expect(screen.getByText('Тикеты CTD')).toBeInTheDocument()
    expect(screen.getByText('Кнопки и вебхуки')).toBeInTheDocument()
    expect(screen.getByText('Приватные комнаты')).toBeInTheDocument()
    expect(screen.getByText('Поставки')).toBeInTheDocument()
  })

  it('loads and displays existing config values', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue({ ...emptyConfig, SERVER_INVITE_LINK: 'https://discord.gg/example' })
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<ConfigPage />)

    await waitFor(() => screen.getByLabelText('Ссылка-приглашение сервера'))
    expect((screen.getByLabelText('Ссылка-приглашение сервера') as HTMLInputElement).value).toBe(
      'https://discord.gg/example',
    )
  })

  it('saves the updated config', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(emptyConfig)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'logs' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const updateSpy = vi.spyOn(client, 'updateConfig').mockResolvedValue(emptyConfig)

    render(<ConfigPage />)

    await waitFor(() => screen.getByLabelText('Канал логов'))
    fireEvent.change(screen.getByLabelText('Канал логов'), { target: { value: '500' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ LOG_CHANNEL_ID: '500' })),
    )
  })

  it('keeps the save button disabled until something changes', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(emptyConfig)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<ConfigPage />)

    await waitFor(() => screen.getByRole('button', { name: 'Сохранить' }))
    expect(screen.getByRole('button', { name: 'Сохранить' })).toBeDisabled()
  })

  it('shows an error when save fails', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(emptyConfig)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'updateConfig').mockRejectedValue(new Error('boom'))

    render(<ConfigPage />)

    await waitFor(() => screen.getByLabelText('Ссылка-приглашение сервера'))
    fireEvent.change(screen.getByLabelText('Ссылка-приглашение сервера'), { target: { value: 'https://discord.gg/x' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => screen.getByText('Не удалось сохранить конфигурацию — проверьте поля'))
  })
})
