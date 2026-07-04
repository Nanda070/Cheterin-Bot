import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AutoRolesPage } from './AutoRoles'

describe('AutoRolesPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders roles with the currently selected ones checked', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([
      { id: '7', name: 'Member', color: '#5865f2', position: 5 },
      { id: '8', name: 'VIP', color: '#5865f2', position: 6 },
    ])
    vi.spyOn(client, 'fetchAutoRoles').mockResolvedValue({ role_ids: ['7'] })

    render(<AutoRolesPage />)

    const memberCheckbox = (await screen.findByLabelText('Member')) as HTMLInputElement
    const vipCheckbox = screen.getByLabelText('VIP') as HTMLInputElement
    expect(memberCheckbox.checked).toBe(true)
    expect(vipCheckbox.checked).toBe(false)
  })

  it('toggles a role and saves the selection', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([
      { id: '7', name: 'Member', color: '#5865f2', position: 5 },
    ])
    vi.spyOn(client, 'fetchAutoRoles').mockResolvedValue({ role_ids: [] })
    const updateSpy = vi.spyOn(client, 'updateAutoRoles').mockResolvedValue({ role_ids: ['7'] })

    render(<AutoRolesPage />)
    fireEvent.click(await screen.findByLabelText('Member'))
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(['7']))
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('shows an error when saving fails', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchAutoRoles').mockResolvedValue({ role_ids: [] })
    vi.spyOn(client, 'updateAutoRoles').mockRejectedValue(new Error('fail'))

    render(<AutoRolesPage />)
    fireEvent.click(await screen.findByText('Сохранить'))

    expect(await screen.findByText('Не удалось сохранить — проверьте, что роли ниже роли бота')).toBeInTheDocument()
  })
})
