import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FunPage } from './Fun'

const emptySettings: client.FunSettings = {
  enabled: false,
  roulette_timeout_minutes: 1,
  roulette_cooldown_sec: 30,
  auto_emoji_enabled: false,
  auto_emoji_chance_percent: 4,
  auto_emoji_min_interval_sec: 300,
  auto_emoji_remove_after_sec: 120,
}

describe('FunPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the module toggle and both roulette cards', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    render(<FunPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByText(/Русская рулетка/)).toBeInTheDocument()
    expect(screen.getByText(/Эмодзи-рулетка/)).toBeInTheDocument()
  })

  it('toggles enabled and saves settings', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue({ ...emptySettings, enabled: true })

    render(<FunPage />)
    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true })))
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('updates timeout and cooldown fields before saving', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue(emptySettings)
    render(<FunPage />)

    fireEvent.change(await screen.findByLabelText(/Таймаут проигравшему/), { target: { value: '10' } })
    fireEvent.change(screen.getByLabelText(/Кулдаун на игрока/), { target: { value: '120' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ roulette_timeout_minutes: 10, roulette_cooldown_sec: 120 }),
      ),
    )
  })

  it('renders the auto-emoji card and saves its settings', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue(emptySettings)
    render(<FunPage />)

    expect(await screen.findByText('✨ Авто-Эмодзи')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Выключено'))
    fireEvent.change(screen.getByLabelText(/Шанс на сообщение/), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ auto_emoji_enabled: true, auto_emoji_chance_percent: 10 }),
      ),
    )
  })

  it('shows an error when loading fails', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockRejectedValue(new Error('fail'))
    render(<FunPage />)
    expect(await screen.findByText('Не удалось загрузить настройки модуля «Развлечения»')).toBeInTheDocument()
  })
})
