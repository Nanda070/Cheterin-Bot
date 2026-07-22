import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithI18n } from '../test/renderWithI18n'
import { LockdownPage } from './Lockdown'

describe('LockdownPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows inactive status', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    renderWithI18n(<LockdownPage />)
    await waitFor(() => expect(screen.getByText(/выключен/i)).toBeInTheDocument())
    expect(screen.getByText('Включить антиспам')).toBeInTheDocument()
  })

  it('activates after confirmation and refreshes status', async () => {
    const statusSpy = vi
      .spyOn(client, 'fetchLockdownStatus')
      .mockResolvedValueOnce({ active: false, role_count: 0 })
      .mockResolvedValueOnce({ active: true, role_count: 3 })
    const activateSpy = vi.spyOn(client, 'activateLockdown').mockResolvedValue()

    renderWithI18n(<LockdownPage />)
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

    renderWithI18n(<LockdownPage />)

    expect(await screen.findByText('rulebreaker')).toBeInTheDocument()
    expect(screen.getByText('mod')).toBeInTheDocument()
    expect(screen.getByText('userC')).toBeInTheDocument()
    expect(screen.getByText('Автоматически')).toBeInTheDocument()
  })

  it('shows an empty state when there is no activity', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])

    renderWithI18n(<LockdownPage />)

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
    vi.spyOn(client, 'fetchSpamSettings').mockResolvedValue({
      limit_with_attachments: 3,
      limit_without_attachments: 5,
      time_window_sec: 60,
    })
    vi.spyOn(client, 'fetchTempbanSettings').mockResolvedValue({
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
    })

    renderWithI18n(<LockdownPage />)
    fireEvent.click(await screen.findByText('Антирейд'))

    expect(await screen.findByText(/выключен по умолчанию/)).toBeInTheDocument()
  })

  it('switches to the Верификация tab', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])
    vi.spyOn(client, 'fetchVerificationSettings').mockResolvedValue({
      enabled: false,
      unverified_role_id: '',
      verified_role_id: '',
      welcome_text: 'Нажмите кнопку ниже.',
    })

    renderWithI18n(<LockdownPage />)
    fireEvent.click(await screen.findByText('Верификация'))

    expect(await screen.findByText(/выключен по умолчанию/)).toBeInTheDocument()
  })
})
