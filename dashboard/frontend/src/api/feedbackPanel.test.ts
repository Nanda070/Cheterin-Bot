import { afterEach, describe, expect, it, vi } from 'vitest'
import { publishFeedbackPanel } from './client'

describe('publishFeedbackPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('POSTs the selected channel id and returns the message id', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true, message_id: '999' }), { status: 200 }),
    )

    const result = await publishFeedbackPanel('500')

    expect(result).toEqual({ ok: true, message_id: '999' })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/feedback-panel/publish')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({ channel_id: '500' })
  })
})
