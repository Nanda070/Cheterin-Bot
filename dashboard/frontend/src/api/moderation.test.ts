import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ApiError,
  banMember,
  fetchLockdownStatus,
  fetchMembers,
  fetchModerationLog,
  grantRole,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('moderation api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchMembers builds query string and returns page', async () => {
    const page = { total: 1, page: 2, page_size: 20, members: [] }
    const fetchMock = vi.fn().mockResolvedValue(okJson(page))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchMembers('sharp', 2)
    expect(result).toEqual(page)
    const url = fetchMock.mock.calls[0][0] as string
    expect(url).toContain('/api/members?')
    expect(url).toContain('search=sharp')
    expect(url).toContain('page=2')
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ credentials: 'include' })
  })

  it('banMember POSTs reason and delete days', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await banMember('42', 'спам', 7)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/members/42/ban',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({ reason: 'спам', delete_message_days: 7 }),
      }),
    )
  })

  it('grantRole POSTs role id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await grantRole('42', '7')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/members/42/roles',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ role_id: '7' }) }),
    )
  })

  it('throws ApiError with status on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 403, json: async () => ({ error: 'forbidden_by_discord' }) }),
    )
    await expect(fetchLockdownStatus()).rejects.toMatchObject({ status: 403 })
    await expect(fetchLockdownStatus()).rejects.toBeInstanceOf(ApiError)
  })

  it('fetchModerationLog unwraps the events array', async () => {
    const events = [
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
    ]
    const fetchMock = vi.fn().mockResolvedValue(okJson({ events }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchModerationLog()
    expect(result).toEqual(events)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/moderation-log')
  })
})
