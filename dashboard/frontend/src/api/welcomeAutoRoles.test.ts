import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  fetchAutoRoles,
  fetchWelcomeSettings,
  updateAutoRoles,
  updateWelcomeSettings,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('welcome and auto-roles api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchWelcomeSettings calls the welcome-settings endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ channel_enabled: true, dm_enabled: false }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchWelcomeSettings()
    expect(result).toEqual({ channel_enabled: true, dm_enabled: false })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/welcome-settings')
  })

  it('updateWelcomeSettings PUTs the toggle values', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ channel_enabled: false, dm_enabled: true }))
    vi.stubGlobal('fetch', fetchMock)

    await updateWelcomeSettings({ channel_enabled: false, dm_enabled: true })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/welcome-settings',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ channel_enabled: false, dm_enabled: true }),
      }),
    )
  })

  it('fetchAutoRoles calls the auto-roles endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ role_ids: ['7', '8'] }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchAutoRoles()
    expect(result).toEqual({ role_ids: ['7', '8'] })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/auto-roles')
  })

  it('updateAutoRoles PUTs the selected role ids', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ role_ids: ['7'] }))
    vi.stubGlobal('fetch', fetchMock)

    await updateAutoRoles(['7'])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auto-roles',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify({ role_ids: ['7'] }) }),
    )
  })
})
