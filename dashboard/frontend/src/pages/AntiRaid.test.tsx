import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithI18n } from '../test/renderWithI18n'
import { AntiRaidPage } from './AntiRaid'

const emptySettings: client.AntiRaidSettings = {
  enabled: false,
  join_window_sec: 10,
  join_threshold: 5,
  min_account_age_hours: 24,
  action_lockdown: true,
  action_slowmode_sec: 0,
  cooldown_minutes: 30,
}

describe('AntiRaidPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders disabled by default', async () => {
    vi.spyOn(client, 'fetchAntiRaidSettings').mockResolvedValue(emptySettings)
    renderWithI18n(<AntiRaidPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByText(/выключен по умолчанию/)).toBeInTheDocument()
  })

  it('toggles and saves settings', async () => {
    vi.spyOn(client, 'fetchAntiRaidSettings').mockResolvedValue(emptySettings)
    const updateSpy = vi
      .spyOn(client, 'updateAntiRaidSettings')
      .mockResolvedValue({ ...emptySettings, enabled: true, join_threshold: 10 })
    renderWithI18n(<AntiRaidPage />)

    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.change(screen.getByLabelText(/Порог входов/), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true, join_threshold: 10 })),
    )
    expect(await screen.findByText('Сохранено')).toBeInTheDocument()
  })

  it('shows an error when loading fails', async () => {
    vi.spyOn(client, 'fetchAntiRaidSettings').mockRejectedValue(new Error('fail'))
    renderWithI18n(<AntiRaidPage />)
    expect(await screen.findByText('Не удалось загрузить настройки модуля «Антирейд»')).toBeInTheDocument()
  })
})
