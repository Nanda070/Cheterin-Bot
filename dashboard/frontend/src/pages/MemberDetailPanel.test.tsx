import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithI18n } from '../test/renderWithI18n'
import { MemberDetailPanel } from './MemberDetailPanel'

const baseDetail: client.MemberDetail = {
  id: '100',
  username: 'fighter',
  display_name: 'Fighter',
  avatar: null,
  joined_at: '2026-01-01T00:00:00Z',
  is_bot: false,
  created_at: '2025-01-01T00:00:00Z',
  roles: [],
  invite_stats: { joins: 0, leaves: 0, invites: 0 },
  feedback_case_count: 0,
}

function mockBaseFetches(warns: client.Warn[] = [], activeCount = 0) {
  vi.spyOn(client, 'fetchMemberDetail').mockResolvedValue(baseDetail)
  vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
  vi.spyOn(client, 'fetchMemberWarns').mockResolvedValue({ warns, active_count: activeCount })
}

describe('MemberDetailPanel warns', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows no-warns message when member has none', async () => {
    mockBaseFetches()
    renderWithI18n(<MemberDetailPanel memberId="100" onClose={() => {}} onActionDone={() => {}} />)

    expect(await screen.findByText('Предупреждения (0)')).toBeInTheDocument()
    expect(screen.getByText('Предупреждений нет.')).toBeInTheDocument()
  })

  it('lists active and removed warns', async () => {
    mockBaseFetches(
      [
        {
          id: 1,
          guild_id: '1',
          user_id: '100',
          reason: 'Спам',
          moderator_id: '10',
          source: 'manual',
          created_at: '2026-01-01T00:00:00Z',
          expires_at: null,
          removed: false,
          removed_by: null,
          removed_at: null,
        },
        {
          id: 2,
          guild_id: '1',
          user_id: '100',
          reason: 'Флуд',
          moderator_id: null,
          source: 'repeated_text',
          created_at: '2026-01-02T00:00:00Z',
          expires_at: null,
          removed: true,
          removed_by: '10',
          removed_at: '2026-01-03T00:00:00Z',
        },
      ],
      1,
    )

    renderWithI18n(<MemberDetailPanel memberId="100" onClose={() => {}} onActionDone={() => {}} />)

    expect(await screen.findByText('Предупреждения (1)')).toBeInTheDocument()
    expect(screen.getByText(/#1 — Спам/)).toBeInTheDocument()
    expect(screen.getByText(/#2 — Флуд/)).toBeInTheDocument()
  })

  it('gives a new warn via the modal', async () => {
    mockBaseFetches()
    const createSpy = vi.spyOn(client, 'createMemberWarn').mockResolvedValue({
      warn: {
        id: 1,
        guild_id: '1',
        user_id: '100',
        reason: 'Нарушение правил',
        moderator_id: '10',
        source: 'manual',
        created_at: '2026-01-01T00:00:00Z',
        expires_at: null,
        removed: false,
        removed_by: null,
        removed_at: null,
      },
      active_count: 1,
    })

    renderWithI18n(<MemberDetailPanel memberId="100" onClose={() => {}} onActionDone={() => {}} />)
    await screen.findByText('Предупреждения (0)')

    fireEvent.click(screen.getByRole('button', { name: 'Выдать предупреждение' }))
    fireEvent.change(screen.getByLabelText('Причина (обязательно)'), { target: { value: 'Нарушение правил' } })
    fireEvent.click(screen.getByRole('button', { name: 'Подтвердить' }))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('100', 'Нарушение правил'))
  })

  it('removes an active warn', async () => {
    mockBaseFetches(
      [
        {
          id: 5,
          guild_id: '1',
          user_id: '100',
          reason: 'Спам',
          moderator_id: '10',
          source: 'manual',
          created_at: '2026-01-01T00:00:00Z',
          expires_at: null,
          removed: false,
          removed_by: null,
          removed_at: null,
        },
      ],
      1,
    )
    const deleteSpy = vi.spyOn(client, 'deleteWarn').mockResolvedValue()

    renderWithI18n(<MemberDetailPanel memberId="100" onClose={() => {}} onActionDone={() => {}} />)
    await screen.findByText(/#5 — Спам/)

    fireEvent.click(screen.getByTitle('Снять предупреждение'))
    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith(5))
  })
})
