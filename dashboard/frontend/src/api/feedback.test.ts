import { afterEach, describe, expect, it, vi } from 'vitest'
import { decideFeedbackCase, fetchFeedbackCaseDetail, fetchFeedbackCases } from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('feedback cases api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchFeedbackCases unwraps the list with no status filter', async () => {
    const cases = [
      {
        case_id: 'PR-0001',
        category_key: 'players',
        category_title: 'Жалоба на участника',
        submitter_id: '50',
        submitter_display: 'submitter',
        status: 'pending',
        created_at: '2026-07-03T00:00:00+00:00',
      },
    ]
    const fetchMock = vi.fn().mockResolvedValue(okJson({ cases }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchFeedbackCases()
    expect(result).toEqual(cases)
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-cases', expect.anything())
  })

  it('fetchFeedbackCases includes the status query param when given', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ cases: [] }))
    vi.stubGlobal('fetch', fetchMock)

    await fetchFeedbackCases('pending')
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-cases?status=pending', expect.anything())
  })

  it('fetchFeedbackCaseDetail GETs by case id', async () => {
    const detail = {
      case_id: 'PR-0001',
      category_key: 'players',
      category_title: 'Жалоба на участника',
      submitter_id: '50',
      submitter_display: 'submitter',
      status: 'pending',
      created_at: '2026-07-03T00:00:00+00:00',
      fields: [{ key: 'offender', label: 'Ник / ID участника', value: 'SomePlayer' }],
      public_channel_id: '500',
      public_message_id: '900',
      thread_id: '700',
    }
    const fetchMock = vi.fn().mockResolvedValue(okJson(detail))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchFeedbackCaseDetail('PR-0001')
    expect(result).toEqual(detail)
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-cases/PR-0001', expect.anything())
  })

  it('decideFeedbackCase POSTs the approved flag', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await decideFeedbackCase('PR-0001', true)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-cases/PR-0001/decide',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ approved: true }) }),
    )
  })
})
