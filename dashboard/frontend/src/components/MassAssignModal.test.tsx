import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { MassAssignModal } from './MassAssignModal'

describe('MassAssignModal', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows an error when starting without selecting a role', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    render(<MassAssignModal open onClose={() => {}} />)

    await waitFor(() => screen.getByText('VIP'))
    fireEvent.click(screen.getByText('Начать'))
    expect(await screen.findByText('Выберите роль')).toBeInTheDocument()
  })

  it('starts a job and shows progress once status resolves', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    vi.spyOn(client, 'startMassAssign').mockResolvedValue('job-1')
    vi.spyOn(client, 'fetchMassAssignStatus').mockResolvedValue({
      status: 'completed',
      total: 5,
      processed: 5,
      succeeded: 5,
      skipped: 0,
      failed: 0,
      errors: [],
    })

    render(<MassAssignModal open onClose={() => {}} />)
    await waitFor(() => screen.getByText('VIP'))

    fireEvent.change(screen.getByLabelText('Роль'), { target: { value: '7' } })
    fireEvent.click(screen.getByLabelText('Все кроме ботов'))
    fireEvent.click(screen.getByText('Начать'))

    await waitFor(() => expect(screen.getByText('Обработано: 5 / 5')).toBeInTheDocument())
    expect(screen.getByText('Готово')).toBeInTheDocument()
  })

  it('requires at least one selected member for target=selected', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    render(<MassAssignModal open onClose={() => {}} />)

    await waitFor(() => screen.getByText('VIP'))
    fireEvent.change(screen.getByLabelText('Роль'), { target: { value: '7' } })
    fireEvent.click(screen.getByLabelText('Выбранные участники'))
    fireEvent.click(screen.getByText('Начать'))

    expect(await screen.findByText('Выберите хотя бы одного участника')).toBeInTheDocument()
  })
})
