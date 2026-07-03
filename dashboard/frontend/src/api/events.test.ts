import { afterEach, describe, expect, it, vi } from 'vitest'
import { closeEvent, deleteEvent, fetchEventDetail, fetchEvents, notifyEventParticipants } from './client'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

describe('events API client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchEvents defaults to no query string', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ events: [] }))
    await fetchEvents()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/events')
  })

  it('fetchEvents appends the status filter', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ events: [] }))
    await fetchEvents('closed')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/events?status=closed')
  })

  it('fetchEventDetail GETs the event by id', async () => {
    const detail = { message_id: '900', type: 'tournament', title: 'T', status: 'open', channel_id: '500', count: 0, description: '', role_reward: null }
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(detail))
    const result = await fetchEventDetail('900')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/events/900')
    expect(result).toEqual(detail)
  })

  it('closeEvent POSTs to the close endpoint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true }))
    await closeEvent('900')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/events/900/close')
    expect(init?.method).toBe('POST')
  })

  it('deleteEvent DELETEs the event', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true }))
    await deleteEvent('900')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/events/900')
    expect(init?.method).toBe('DELETE')
  })

  it('notifyEventParticipants POSTs the message and returns counts', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true, success: 3, failed: 1 }))
    const result = await notifyEventParticipants('900', 'Hello')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/events/900/notify')
    expect(JSON.parse(init?.body as string)).toEqual({ message: 'Hello' })
    expect(result).toEqual({ success: 3, failed: 1 })
  })
})
