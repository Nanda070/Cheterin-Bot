import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createReactionRole,
  deleteReactionRole,
  fetchChannels,
  fetchEmojis,
  fetchReactionRoles,
  updateReactionRole,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('reaction roles api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchReactionRoles unwraps the list', async () => {
    const entries = [{ message_id: '1', channel_id: '2', pairs: [] }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ reaction_roles: entries })))
    const result = await fetchReactionRoles()
    expect(result).toEqual(entries)
  })

  it('createReactionRole POSTs channel_id/message_id/pairs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '1', channel_id: '2', pairs: [] }))
    vi.stubGlobal('fetch', fetchMock)

    await createReactionRole('2', '1', [{ emoji: '📖', role_id: '7' }])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/reaction-roles',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ channel_id: '2', message_id: '1', pairs: [{ emoji: '📖', role_id: '7' }] }),
      }),
    )
  })

  it('updateReactionRole PUTs only pairs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '1', channel_id: '2', pairs: [] }))
    vi.stubGlobal('fetch', fetchMock)

    await updateReactionRole('1', [{ emoji: '✅', role_id: '8' }])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/reaction-roles/1',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify({ pairs: [{ emoji: '✅', role_id: '8' }] }) }),
    )
  })

  it('deleteReactionRole DELETEs by message id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await deleteReactionRole('1')
    expect(fetchMock).toHaveBeenCalledWith('/api/reaction-roles/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('fetchEmojis unwraps the list', async () => {
    const emojis = [{ id: '20', name: 'wave', url: 'https://cdn.example/emojis/20.png' }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ emojis })))
    expect(await fetchEmojis()).toEqual(emojis)
  })

  it('fetchChannels unwraps the list', async () => {
    const channels = [
      { id: '500', name: 'general', bot_can_view: true, bot_can_send: false },
    ]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ channels })))
    expect(await fetchChannels()).toEqual(channels)
  })
})
