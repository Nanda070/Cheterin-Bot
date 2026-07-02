import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { LockdownPage } from './Lockdown'

describe('LockdownPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows inactive status', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    render(<LockdownPage />)
    await waitFor(() => expect(screen.getByText(/выключен/i)).toBeInTheDocument())
    expect(screen.getByText('Включить антиспам')).toBeInTheDocument()
  })

  it('activates after confirmation and refreshes status', async () => {
    const statusSpy = vi
      .spyOn(client, 'fetchLockdownStatus')
      .mockResolvedValueOnce({ active: false, role_count: 0 })
      .mockResolvedValueOnce({ active: true, role_count: 3 })
    const activateSpy = vi.spyOn(client, 'activateLockdown').mockResolvedValue()

    render(<LockdownPage />)
    await waitFor(() => screen.getByText('Включить антиспам'))
    fireEvent.click(screen.getByText('Включить антиспам'))
    fireEvent.click(screen.getByText('Подтвердить'))

    await waitFor(() => expect(activateSpy).toHaveBeenCalled())
    await waitFor(() => expect(statusSpy).toHaveBeenCalledTimes(2))
    expect(screen.getByText(/включён/i)).toBeInTheDocument()
  })
})
