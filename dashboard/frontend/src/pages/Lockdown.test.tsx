import { fireEvent, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithI18n } from '../test/renderWithI18n'
import { LockdownPage } from './Lockdown'

function renderLockdown(initialEntry = '/lockdown') {
  return renderWithI18n(
    <MemoryRouter initialEntries={[initialEntry]}>
      <LockdownPage />
    </MemoryRouter>,
  )
}

describe('LockdownPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows inactive status', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    renderLockdown()
    await waitFor(() => expect(screen.getByText(/выключен/i)).toBeInTheDocument())
    expect(screen.getByText('Включить антиспам')).toBeInTheDocument()
  })

  it('activates after confirmation and refreshes status', async () => {
    const statusSpy = vi
      .spyOn(client, 'fetchLockdownStatus')
      .mockResolvedValueOnce({ active: false, role_count: 0 })
      .mockResolvedValueOnce({ active: true, role_count: 3 })
    const activateSpy = vi.spyOn(client, 'activateLockdown').mockResolvedValue()

    renderLockdown()
    await waitFor(() => screen.getByText('Включить антиспам'))
    fireEvent.click(screen.getByText('Включить антиспам'))
    fireEvent.click(screen.getByText('Подтвердить'))

    await waitFor(() => expect(activateSpy).toHaveBeenCalled())
    await waitFor(() => expect(statusSpy).toHaveBeenCalledTimes(2))
    expect(screen.getByText(/включён/i)).toBeInTheDocument()
  })

  it('renders moderation activity entries', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([
      {
        type: 'manual_ban',
        timestamp: '2026-07-04T12:00:00+00:00',
        user_id: '70',
        user_display: 'rulebreaker',
        moderator_id: '10',
        moderator_display: 'mod',
        reason: 'спам',
        extra: '',
      },
      {
        type: 'tempban',
        timestamp: '2026-07-04T11:00:00+00:00',
        user_id: '5',
        user_display: 'userC',
        moderator_id: null,
        moderator_display: null,
        reason: 'Автоматический Tempban (Сброс сообщений за 20 мин.)',
        extra: '',
      },
    ])

    renderLockdown()

    expect(await screen.findByText('rulebreaker')).toBeInTheDocument()
    expect(screen.getByText('mod')).toBeInTheDocument()
    expect(screen.getByText('userC')).toBeInTheDocument()
    expect(screen.getByText('Автоматически')).toBeInTheDocument()
  })

  it('renders without crashing for types missing from the old icon map', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([
      {
        type: 'manual_mute',
        timestamp: '2026-07-04T12:00:00+00:00',
        user_id: '71',
        user_display: 'mutedUser',
        moderator_id: '10',
        moderator_display: 'mod',
        reason: 'timeout',
        extra: '',
      },
      {
        type: 'automod_invites',
        timestamp: '2026-07-04T11:30:00+00:00',
        user_id: '72',
        user_display: 'inviteSpammer',
        moderator_id: null,
        moderator_display: null,
        reason: 'invite link',
        extra: '',
      },
      {
        type: 'future_unknown_event',
        timestamp: '2026-07-04T11:00:00+00:00',
        user_id: '73',
        user_display: 'mystery',
        moderator_id: null,
        moderator_display: null,
        reason: 'new backend type',
        extra: '',
      },
    ])

    renderLockdown()

    expect(await screen.findByText('mutedUser')).toBeInTheDocument()
    expect(screen.getByText('inviteSpammer')).toBeInTheDocument()
    expect(screen.getByText('mystery')).toBeInTheDocument()
    expect(screen.getByText('Таймаут (дашборд)')).toBeInTheDocument()
    expect(screen.getByText('Автомод: приглашения')).toBeInTheDocument()
    expect(screen.getByText('future_unknown_event')).toBeInTheDocument()
  })

  it('shows an empty state when there is no activity', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])

    renderLockdown()

    expect(await screen.findByText('Активности пока нет.')).toBeInTheDocument()
  })

  it('switches to the Антирейд tab', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])
    vi.spyOn(client, 'fetchAntiRaidSettings').mockResolvedValue({
      enabled: false,
      join_window_sec: 10,
      join_threshold: 5,
      min_account_age_hours: 24,
      action_lockdown: true,
      action_slowmode_sec: 0,
      cooldown_minutes: 30,
    })

    renderLockdown()
    fireEvent.click(await screen.findByText('Антирейд'))

    expect(await screen.findByText(/выключен по умолчанию/)).toBeInTheDocument()
  })

  it('switches to the Анти-спам tab', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])
    vi.spyOn(client, 'fetchSpamSettings').mockResolvedValue({
      limit_with_attachments: 3,
      limit_without_attachments: 5,
      time_window_sec: 60,
    })
    const { EMPTY_BOT_CONFIG } = await import('../config/botConfigDefaults')
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(EMPTY_BOT_CONFIG)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderLockdown()
    fireEvent.click(await screen.findByRole('button', { name: 'Анти-спам' }))

    expect(await screen.findByText('Детектор массовых тегов')).toBeInTheDocument()
  })

  it('switches to the Spam traps tab', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])
    vi.spyOn(client, 'fetchTempbanSettings').mockResolvedValue({
      action: 'softban',
      dm_enabled: true,
      dm_message: '',
      log_enabled: true,
      log_message: '',
      unban_reason: '',
      warning_message: '',
      warning_thumbnail_url: '',
      warning_message_id: '',
      ban_count: 0,
    })
    const { EMPTY_BOT_CONFIG } = await import('../config/botConfigDefaults')
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(EMPTY_BOT_CONFIG)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderLockdown()
    fireEvent.click(await screen.findByRole('button', { name: 'Ловушки от Спама' }))

    expect(await screen.findByText('Сообщения ловушек от спама')).toBeInTheDocument()
  })

  it('switches to the Верификация tab', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])
    vi.spyOn(client, 'fetchVerificationSettings').mockResolvedValue({
      enabled: false,
      unverified_role_id: '',
      verified_role_id: '',
      welcome_text: 'Нажмите кнопку ниже.',
      rules_consent_enabled: false,
      reverify_enabled: false,
      reverify_days: 30,
    })

    renderLockdown()
    fireEvent.click(await screen.findByText('Верификация'))

    expect(await screen.findByText(/выключен по умолчанию/)).toBeInTheDocument()
  })
})
