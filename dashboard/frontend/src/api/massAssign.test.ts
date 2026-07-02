import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchMassAssignStatus, startMassAssign } from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('mass assign api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('startMassAssign posts target and omits member_ids when not selected', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ job_id: 'job-1' }))
    vi.stubGlobal('fetch', fetchMock)

    const jobId = await startMassAssign('7', 'all_except_bots')
    expect(jobId).toBe('job-1')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/roles/7/mass-assign',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ target: 'all_except_bots' }),
      }),
    )
  })

  it('startMassAssign includes member_ids for selected target', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ job_id: 'job-2' }))
    vi.stubGlobal('fetch', fetchMock)

    await startMassAssign('7', 'selected', ['1', '2'])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/roles/7/mass-assign',
      expect.objectContaining({
        body: JSON.stringify({ target: 'selected', member_ids: ['1', '2'] }),
      }),
    )
  })

  it('fetchMassAssignStatus GETs the status endpoint', async () => {
    const payload = {
      status: 'running',
      total: 10,
      processed: 3,
      succeeded: 3,
      skipped: 0,
      failed: 0,
      errors: [],
    }
    const fetchMock = vi.fn().mockResolvedValue(okJson(payload))
    vi.stubGlobal('fetch', fetchMock)

    const status = await fetchMassAssignStatus('job-1')
    expect(status).toEqual(payload)
    expect(fetchMock).toHaveBeenCalledWith('/api/roles/mass-assign/job-1', expect.objectContaining({ credentials: 'include' }))
  })
})
