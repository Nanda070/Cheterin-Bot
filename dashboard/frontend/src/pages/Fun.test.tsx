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

const emptyWordle: client.WordleSettings = {
  enabled: false,
  channel_id: '',
  announce_time: '09:00',
}

function mockWordle() {
  vi.spyOn(client, 'fetchWordleSettings').mockResolvedValue(emptyWordle)
}

describe('FunPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the module toggle and both roulette cards', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockWordle()
    render(<FunPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByText(/Русская рулетка/)).toBeInTheDocument()
    expect(screen.getByText(/Эмодзи-рулетка/)).toBeInTheDocument()
  })

  it('toggles enabled and saves settings', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockWordle()
    vi.spyOn(client, 'updateWordleSettings').mockResolvedValue(emptyWordle)
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue({ ...emptySettings, enabled: true })

    render(<FunPage />)
    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true })))
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('updates timeout and cooldown fields before saving', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockWordle()
    vi.spyOn(client, 'updateWordleSettings').mockResolvedValue(emptyWordle)
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
    mockWordle()
    vi.spyOn(client, 'updateWordleSettings').mockResolvedValue(emptyWordle)
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

  it('renders the wordle card and saves its settings', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockWordle()
    vi.spyOn(client, 'updateFunSettings').mockResolvedValue(emptySettings)
    const wordleSpy = vi
      .spyOn(client, 'updateWordleSettings')
      .mockResolvedValue({ enabled: true, channel_id: '555', announce_time: '18:30' })
    render(<FunPage />)

    expect(await screen.findByText(/Вордл — \/вордл/)).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Вордл выключен'))
    fireEvent.change(screen.getByLabelText(/ID канала для анонсов/), { target: { value: '555' } })
    fireEvent.change(screen.getByLabelText(/Время ежедневного анонса/), { target: { value: '18:30' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(wordleSpy).toHaveBeenCalledWith(
        expect.objectContaining({ enabled: true, channel_id: '555', announce_time: '18:30' }),
      ),
    )
  })

  it('shows an error when loading fails', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockRejectedValue(new Error('fail'))
    mockWordle()
    render(<FunPage />)
    expect(await screen.findByText('Не удалось загрузить настройки модуля «Развлечения»')).toBeInTheDocument()
  })
})
