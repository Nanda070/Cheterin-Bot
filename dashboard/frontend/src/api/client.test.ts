import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchCurrentUser, logout, loginUrl } from './client'

describe('client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns null when the API responds 401', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
    const user = await fetchCurrentUser()
    expect(user).toBeNull()
  })

  it('returns the user object when the API responds 200', async () => {
    const payload = { id: '1', username: 'tester', avatar: null, is_admin: false }
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload }),
    )
    const user = await fetchCurrentUser()
    expect(user).toEqual(payload)
  })

  it('throws on unexpected error statuses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))
    await expect(fetchCurrentUser()).rejects.toThrow()
  })

  it('logout posts to the logout endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true })
    vi.stubGlobal('fetch', fetchMock)
    await logout()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/logout',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('loginUrl points at the login route', () => {
    expect(loginUrl()).toBe('/api/auth/login')
  })
})
