import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { LockdownPage } from './Lockdown'

describe('LockdownPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows inactive status', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    render(<LockdownPage />)
    await waitFor(() => expect(screen.getByText(/выключен/i)).toBeInTheDocument())
    expect(screen.getByText('Включить антиспам')).toBeInTheDocument()
  })

  it('activates after confirmation and refreshes status', async () => {
    const statusSpy = vi
      .spyOn(client, 'fetchLockdownStatus')
      .mockResolvedValueOnce({ active: false, role_count: 0 })
      .mockResolvedValueOnce({ active: true, role_count: 3 })
    const activateSpy = vi.spyOn(client, 'activateLockdown').mockResolvedValue()

    render(<LockdownPage />)
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

    render(<LockdownPage />)

    expect(await screen.findByText('rulebreaker')).toBeInTheDocument()
    expect(screen.getByText('mod')).toBeInTheDocument()
    expect(screen.getByText('userC')).toBeInTheDocument()
    expect(screen.getByText('Автоматически')).toBeInTheDocument()
  })

  it('shows an empty state when there is no activity', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])

    render(<LockdownPage />)

    expect(await screen.findByText('Активности пока нет.')).toBeInTheDocument()
  })
})
