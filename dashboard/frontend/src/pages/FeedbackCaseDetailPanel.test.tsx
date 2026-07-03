import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackCaseDetailPanel } from './FeedbackCaseDetailPanel'

const sampleDetail: client.FeedbackCaseDetail = {
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

describe('FeedbackCaseDetailPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows the case fields and category title', async () => {
    vi.spyOn(client, 'fetchFeedbackCaseDetail').mockResolvedValue(sampleDetail)

    render(<FeedbackCaseDetailPanel caseId="PR-0001" onClose={() => {}} onDecided={() => {}} />)

    await waitFor(() =>
      screen.getByText((_, element) => element?.textContent === 'Жалоба на участника · PR-0001'),
    )
    expect(screen.getByText('SomePlayer')).toBeInTheDocument()
  })

  it('accepts a pending case', async () => {
    vi.spyOn(client, 'fetchFeedbackCaseDetail').mockResolvedValue(sampleDetail)
    const decideSpy = vi.spyOn(client, 'decideFeedbackCase').mockResolvedValue(undefined)
    const onDecided = vi.fn()

    render(<FeedbackCaseDetailPanel caseId="PR-0001" onClose={() => {}} onDecided={onDecided} />)

    await waitFor(() => screen.getByText('Принять'))
    fireEvent.click(screen.getByText('Принять'))

    await waitFor(() => expect(decideSpy).toHaveBeenCalledWith('PR-0001', true))
    await waitFor(() => expect(onDecided).toHaveBeenCalled())
  })

  it('disables decision buttons when the case is already decided', async () => {
    vi.spyOn(client, 'fetchFeedbackCaseDetail').mockResolvedValue({ ...sampleDetail, status: 'approved' })

    render(<FeedbackCaseDetailPanel caseId="PR-0001" onClose={() => {}} onDecided={() => {}} />)

    await waitFor(() => screen.getByText('Принять'))
    expect(screen.getByText('Принять')).toBeDisabled()
    expect(screen.getByText('Отклонить')).toBeDisabled()
  })
})
