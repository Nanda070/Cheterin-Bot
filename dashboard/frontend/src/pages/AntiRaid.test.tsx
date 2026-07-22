import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithI18n } from '../test/renderWithI18n'
import { AntiRaidPage } from './AntiRaid'

const emptySettings: client.AntiRaidSettings = {
  enabled: false,
  join_window_sec: 10,
  join_threshold: 5,
  min_account_age_hours: 24,
  action_lockdown: true,
  action_slowmode_sec: 0,
  cooldown_minutes: 30,
}

const emptyTempban: client.TempbanSettings = {
  dm_enabled: true,
  dm_message: '',
  log_enabled: true,
  log_embed: {
    title: '',
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
  unban_reason: '',
}

const emptySpam: client.SpamSettings = {
  limit_with_attachments: 3,
  limit_without_attachments: 5,
  time_window_sec: 60,
}

function mockAntiRaidLoads() {
  vi.spyOn(client, 'fetchAntiRaidSettings').mockResolvedValue(emptySettings)
  vi.spyOn(client, 'fetchSpamSettings').mockResolvedValue(emptySpam)
  vi.spyOn(client, 'fetchTempbanSettings').mockResolvedValue(emptyTempban)
}

describe('AntiRaidPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders disabled by default', async () => {
    mockAntiRaidLoads()
    renderWithI18n(<AntiRaidPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByText(/выключен по умолчанию/)).toBeInTheDocument()
  })

  it('toggles and saves settings', async () => {
    mockAntiRaidLoads()
    vi.spyOn(client, 'fetchConfig').mockResolvedValue({
      LOG_CHANNEL_ID: '',
      SPAM_EXCEPTION_CHANNELS: [],
      TEMPBAN_CHANNEL_ID: '',
      TEMPBAN_LOG_CHANNEL_ID: '',
      SPAM_LOG_CHANNEL_ID: '',
      SPAM_LOG_ROLE_ID: '',
      WELCOME_CHANNEL_ID: '',
      INVITE_LOG_CHANNEL_ID: '',
      ANNOUNCEMENTS_CHANNEL_ID: '',
      RULES_CHANNEL_ID: '',
      ROLES_CHANNEL_ID: '',
      SEARCH_PLAYERS_CHANNEL_ID: '',
      BUTTON_CREATE_ALLOWED_ROLES: [],
      BUTTON_WEBHOOK_URL: '',
      BUTTON_WEBHOOK_USERNAME: '',
      BUTTON_WEBHOOK_AVATAR_URL: '',
      SERVER_INVITE_LINK: '',
      VOICE_LOBBY_CHANNEL_ID: '',
      VOICE_PANEL_CHANNEL_ID: '',
      VOICE_LOG_CHANNEL_ID: '',
      VOICE_PANEL_THUMB_URL: '',
      SUPPLY_ROLE_ID: '',
      SUPPLY_VOICE_CHANNEL_ID: '',
      SUPPLY_LOG_CHANNEL_ID: '',
      SUPPLY_REMINDER_MINUTES: '',
    })
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const updateSpy = vi
      .spyOn(client, 'updateAntiRaidSettings')
      .mockResolvedValue({ ...emptySettings, enabled: true, join_threshold: 10 })
    renderWithI18n(<AntiRaidPage />)

    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.change(screen.getByLabelText(/Порог входов/), { target: { value: '10' } })
    fireEvent.click(screen.getAllByRole('button', { name: 'Сохранить' })[0])

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true, join_threshold: 10 })),
    )
    expect(await screen.findByText('Сохранено')).toBeInTheDocument()
  })

  it('shows an error when loading fails', async () => {
    vi.spyOn(client, 'fetchAntiRaidSettings').mockRejectedValue(new Error('fail'))
    vi.spyOn(client, 'fetchTempbanSettings').mockRejectedValue(new Error('fail'))
    renderWithI18n(<AntiRaidPage />)
    expect(await screen.findByText('Не удалось загрузить настройки модуля «Антирейд»')).toBeInTheDocument()
  })
})
