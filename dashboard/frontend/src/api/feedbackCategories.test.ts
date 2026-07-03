import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createFeedbackCategory,
  deleteFeedbackCategory,
  fetchFeedbackCategories,
  updateFeedbackCategory,
  type FeedbackCategorySpec,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

const sampleSpec: FeedbackCategorySpec = {
  key: 'players',
  title: 'Жалоба на участника',
  button_label: 'Жалоба на участника',
  channel_id: '500',
  case_prefix: 'PR',
  case_title: 'Жалоба на участника',
  thread_name: 'player-report',
  review_role_ids: ['111'],
  approved_text: 'Участник наказан.',
  denied_text: 'Жалоба отклонена.',
  modal_title: 'Жалоба на участника',
  fields: [{ key: 'offender', label: 'Ник участника', style: 'short', required: true, max_length: 120 }],
  mini_summary_key: 'offender',
}

describe('feedback categories api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchFeedbackCategories unwraps the list', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ categories: [sampleSpec] }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchFeedbackCategories()
    expect(result).toEqual([sampleSpec])
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-categories', expect.anything())
  })

  it('createFeedbackCategory POSTs the full spec including key', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson(sampleSpec))
    vi.stubGlobal('fetch', fetchMock)

    await createFeedbackCategory(sampleSpec)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-categories',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(sampleSpec) }),
    )
  })

  it('updateFeedbackCategory PUTs by key with the spec minus key', async () => {
    const { key, ...rest } = sampleSpec
    const fetchMock = vi.fn().mockResolvedValue(okJson(sampleSpec))
    vi.stubGlobal('fetch', fetchMock)

    await updateFeedbackCategory(key, rest)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-categories/players',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify(rest) }),
    )
  })

  it('deleteFeedbackCategory DELETEs by key', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await deleteFeedbackCategory('players')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-categories/players',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })
})
