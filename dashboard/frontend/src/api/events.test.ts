import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from './client'
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

  it('createEvent POSTs the full spec and returns the created event', async () => {
    const spec: client.CreateEventSpec = {
      channel_id: '500',
      type: 'tournament',
      title: 'Летний турнир',
      description: 'desc',
      banner_url: '',
      ping: 'none',
      mode: 'solo',
      require_info: false,
      max_limit: 0,
      team_size: 5,
      role_reward: null,
      options: [],
      multi_select: false,
    }
    const created = { message_id: '900', type: 'tournament', title: 'Летний турнир', status: 'open', channel_id: '500', count: 0, description: 'desc', role_reward: null }
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(created, 201))

    const result = await client.createEvent(spec)

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/events')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual(spec)
    expect(result).toEqual(created)
  })

  it('createEvent sends poll-shaped specs unchanged', async () => {
    const spec: client.CreateEventSpec = {
      channel_id: '500',
      type: 'poll',
      title: 'Опрос дня',
      description: 'desc',
      banner_url: '',
      ping: 'none',
      mode: 'solo',
      require_info: false,
      max_limit: 0,
      team_size: 5,
      role_reward: null,
      options: ['Да', 'Нет'],
      multi_select: true,
    }
    const created = { message_id: '901', type: 'poll', title: 'Опрос дня', status: 'open', channel_id: '500', count: 0, description: 'desc', role_reward: null }
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(created, 201))

    await client.createEvent(spec)

    const [, init] = fetchMock.mock.calls[0]
    expect(JSON.parse(init?.body as string).options).toEqual(['Да', 'Нет'])
  })
})
