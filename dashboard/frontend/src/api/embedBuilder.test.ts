import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createEmbedMessage,
  fetchEmbedMessage,
  saveEmbedTemplatesBulk,
  updateEmbedMessage,
  type EmbedMessagePayload,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

const samplePayload: EmbedMessagePayload = {
  content: 'hi',
  embeds: [
    {
      title: 'T',
      description: '',
      url: '',
      color: '',
      author: { name: '', url: '', icon_url: '' },
      footer: { text: '', icon_url: '' },
      image: { url: '' },
      thumbnail: { url: '' },
      timestamp: null,
      fields: [],
    },
  ],
  role_ids: ['7'],
}

describe('embed builder api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('createEmbedMessage POSTs channel_id alongside the payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '999', channel_id: '500' }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createEmbedMessage('500', samplePayload)
    expect(result).toEqual({ message_id: '999', channel_id: '500' })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/embed-messages',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ channel_id: '500', ...samplePayload }),
      }),
    )
  })

  it('fetchEmbedMessage GETs by channel and message id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson(samplePayload))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchEmbedMessage('500', '999')
    expect(result).toEqual(samplePayload)
    expect(fetchMock).toHaveBeenCalledWith('/api/embed-messages/500/999', expect.anything())
  })

  it('updateEmbedMessage PUTs the payload without channel_id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '999', channel_id: '500' }))
    vi.stubGlobal('fetch', fetchMock)

    await updateEmbedMessage('500', '999', samplePayload)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/embed-messages/500/999',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify(samplePayload) }),
    )
  })

  it('saveEmbedTemplatesBulk POSTs the templates list', async () => {
    const outcome = { created: [], skipped: [{ name: 'A', reason: 'duplicate_name' }] }
    const fetchMock = vi.fn().mockResolvedValue(okJson(outcome))
    vi.stubGlobal('fetch', fetchMock)

    const templates = [{ name: 'A', content: 'c', embeds: samplePayload.embeds }]
    expect(await saveEmbedTemplatesBulk(templates)).toEqual(outcome)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/embed-templates/bulk',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ templates }) }),
    )
  })
})
