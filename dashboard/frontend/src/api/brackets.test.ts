import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createBracket,
  deleteBracket,
  disableBracketShare,
  enableBracketShare,
  fetchBrackets,
  fetchBracketDetail,
  fetchEventEntries,
  fetchPublicBracket,
  setBracketMatchWinner,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('brackets api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchBrackets unwraps the brackets array', async () => {
    const brackets = [{ id: '1', title: 'T1', source_event_id: null, entry_count: 4, created_at: '2026-07-04' }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ brackets })))
    const result = await fetchBrackets()
    expect(result).toEqual(brackets)
  })

  it('fetchBracketDetail calls the detail endpoint', async () => {
    const detail = { id: '1', title: 'T1', source_event_id: null, entries: ['A', 'B'], rounds: [], share_token: null }
    const fetchMock = vi.fn().mockResolvedValue(okJson(detail))
    vi.stubGlobal('fetch', fetchMock)
    const result = await fetchBracketDetail('1')
    expect(result).toEqual(detail)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/brackets/1')
  })

  it('fetchEventEntries calls the preview endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ entries: ['Alpha', 'Beta'] }))
    vi.stubGlobal('fetch', fetchMock)
    const result = await fetchEventEntries('900')
    expect(result).toEqual(['Alpha', 'Beta'])
    expect(fetchMock.mock.calls[0][0]).toBe('/api/brackets/entries-from-event/900')
  })

  it('createBracket POSTs title, entries, and source_event_id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({ id: '1', title: 'T1', source_event_id: null, entries: ['A', 'B'], rounds: [], share_token: null }),
    )
    vi.stubGlobal('fetch', fetchMock)
    await createBracket('T1', ['A', 'B'], null)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/brackets',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ title: 'T1', entries: ['A', 'B'], source_event_id: null }),
      }),
    )
  })

  it('deleteBracket DELETEs the bracket', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    await deleteBracket('1')
    expect(fetchMock).toHaveBeenCalledWith('/api/brackets/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('setBracketMatchWinner POSTs the winner', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({ id: '1', title: 'T1', source_event_id: null, entries: [], rounds: [], share_token: null }),
    )
    vi.stubGlobal('fetch', fetchMock)
    await setBracketMatchWinner('1', 0, 2, 'a')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/brackets/1/matches/0/2/winner',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ winner: 'a' }) }),
    )
  })

  it('enableBracketShare returns the token', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ share_token: 'abc' })))
    const token = await enableBracketShare('1')
    expect(token).toBe('abc')
  })

  it('disableBracketShare DELETEs the share endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    await disableBracketShare('1')
    expect(fetchMock).toHaveBeenCalledWith('/api/brackets/1/share', expect.objectContaining({ method: 'DELETE' }))
  })

  it('fetchPublicBracket calls the public endpoint', async () => {
    const detail = { id: '1', title: 'T1', source_event_id: null, entries: [], rounds: [], share_token: 'abc' }
    const fetchMock = vi.fn().mockResolvedValue(okJson(detail))
    vi.stubGlobal('fetch', fetchMock)
    const result = await fetchPublicBracket('abc')
    expect(result).toEqual(detail)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/public/brackets/abc')
  })
})
