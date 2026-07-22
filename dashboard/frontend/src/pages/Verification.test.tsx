import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithI18n } from '../test/renderWithI18n'
import { VerificationPage } from './Verification'

const emptySettings: client.VerificationSettings = {
  enabled: false,
  unverified_role_id: '',
  verified_role_id: '',
  welcome_text: 'Нажмите кнопку ниже.',
}

describe('VerificationPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders disabled by default', async () => {
    vi.spyOn(client, 'fetchVerificationSettings').mockResolvedValue(emptySettings)
    renderWithI18n(<VerificationPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByText(/выключен по умолчанию/)).toBeInTheDocument()
  })

  it('toggles and saves settings', async () => {
    vi.spyOn(client, 'fetchVerificationSettings').mockResolvedValue(emptySettings)
    const updateSpy = vi
      .spyOn(client, 'updateVerificationSettings')
      .mockResolvedValue({ ...emptySettings, enabled: true, verified_role_id: '222' })
    renderWithI18n(<VerificationPage />)

    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.change(screen.getByLabelText(/ID роли «Verified»/), { target: { value: '222' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true, verified_role_id: '222' })),
    )
    expect(await screen.findByText('Сохранено')).toBeInTheDocument()
  })

  it('shows an error when loading fails', async () => {
    vi.spyOn(client, 'fetchVerificationSettings').mockRejectedValue(new Error('fail'))
    renderWithI18n(<VerificationPage />)
    expect(await screen.findByText('Не удалось загрузить настройки модуля «Верификация»')).toBeInTheDocument()
  })
})
