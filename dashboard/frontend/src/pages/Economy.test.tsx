import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EconomyPage } from './Economy'

const emptySettings: client.EconomySettings = {
  enabled: false,
  currency_name: 'монеты',
  currency_emoji: '🪙',
  text_rate_percent: 50,
  voice_rate_percent: 50,
  transfer_enabled: true,
  transfer_fee_percent: 0,
  roulette_bets_enabled: true,
  roulette_max_bet: 1000,
  daily_bonus_enabled: true,
  daily_base_amount: 50,
  daily_growth_per_day: 25,
  daily_max_streak_days: 7,
  shop_items: [],
}

const emptyCasino: client.CasinoSettings = {
  enabled: false,
  house_edge_percent: 5,
  cooldown_sec: 5,
  min_bet: 10,
  max_bet: 5000,
}

function mockCasino() {
  vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptyCasino)
}

describe('EconomyPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders settings cards and top', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([
      { user_id: '20', display_name: 'Rich', balance: 300 },
    ])
    render(<EconomyPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByText('Валюта и начисление')).toBeInTheDocument()
    expect(screen.getByText(/Магазин — \/магазин/)).toBeInTheDocument()
    expect(screen.getByText(/Казино/)).toBeInTheDocument()
    expect(await screen.findByText('Rich')).toBeInTheDocument()
  })

  it('saves updated settings', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'updateCasinoSettings').mockResolvedValue(emptyCasino)
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([])
    const updateSpy = vi
      .spyOn(client, 'updateEconomySettings')
      .mockResolvedValue({ ...emptySettings, enabled: true, text_rate_percent: 100 })
    render(<EconomyPage />)

    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.change(screen.getByLabelText(/Монет за текстовый XP/), { target: { value: '100' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true, text_rate_percent: 100 })),
    )
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('adds and removes shop items', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'updateCasinoSettings').mockResolvedValue(emptyCasino)
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([])
    const updateSpy = vi.spyOn(client, 'updateEconomySettings').mockResolvedValue(emptySettings)
    render(<EconomyPage />)

    fireEvent.click(await screen.findByRole('button', { name: /Добавить товар/ }))
    fireEvent.change(screen.getByLabelText('Название товара 1'), { target: { value: 'VIP' } })
    fireEvent.change(screen.getByLabelText('ID роли товара 1'), { target: { value: '777' } })
    fireEvent.change(screen.getByLabelText('Цена товара 1'), { target: { value: '500' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          shop_items: [expect.objectContaining({ name: 'VIP', role_id: 777, price: 500 })],
        }),
      ),
    )
  })

  it('adds a title cosmetic item by switching the type selector', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'updateCasinoSettings').mockResolvedValue(emptyCasino)
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([])
    const updateSpy = vi.spyOn(client, 'updateEconomySettings').mockResolvedValue(emptySettings)
    render(<EconomyPage />)

    fireEvent.click(await screen.findByRole('button', { name: /Добавить товар/ }))
    fireEvent.change(screen.getByLabelText('Тип товара 1'), { target: { value: 'title' } })
    fireEvent.change(screen.getByLabelText('Текст титула товара 1'), { target: { value: 'Легенда' } })
    fireEvent.change(screen.getByLabelText('Цена товара 1'), { target: { value: '300' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          shop_items: [expect.objectContaining({ type: 'title', title_text: 'Легенда', price: 300 })],
        }),
      ),
    )
  })

  it('adds a frame_color cosmetic item', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'updateCasinoSettings').mockResolvedValue(emptyCasino)
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([])
    const updateSpy = vi.spyOn(client, 'updateEconomySettings').mockResolvedValue(emptySettings)
    render(<EconomyPage />)

    fireEvent.click(await screen.findByRole('button', { name: /Добавить товар/ }))
    fireEvent.change(screen.getByLabelText('Тип товара 1'), { target: { value: 'frame_color' } })
    fireEvent.change(screen.getByLabelText('Hex-код рамки товара 1'), { target: { value: '#FF00AA' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          shop_items: [expect.objectContaining({ type: 'frame_color', color_hex: '#FF00AA' })],
        }),
      ),
    )
  })

  it('applies balance adjustment from top list', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([
      { user_id: '20', display_name: 'Rich', balance: 300 },
    ])
    const setSpy = vi.spyOn(client, 'setEconomyBalance').mockResolvedValue({ user_id: '20', balance: 50 })
    render(<EconomyPage />)

    fireEvent.change(await screen.findByLabelText('Новый баланс Rich'), { target: { value: '50' } })
    fireEvent.click(screen.getByRole('button', { name: 'Применить' }))

    await waitFor(() => expect(setSpy).toHaveBeenCalledWith('20', 50))
  })

  it('renders and saves casino settings', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'updateEconomySettings').mockResolvedValue(emptySettings)
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([])
    const casinoSpy = vi
      .spyOn(client, 'updateCasinoSettings')
      .mockResolvedValue({ ...emptyCasino, enabled: true, house_edge_percent: 10 })
    render(<EconomyPage />)

    fireEvent.click(await screen.findByLabelText('Выключено'))
    fireEvent.change(screen.getByLabelText(/Преимущество казино/), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(casinoSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true, house_edge_percent: 10 })),
    )
  })

  it('renders and saves the daily bonus card', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptySettings)
    mockCasino()
    vi.spyOn(client, 'updateCasinoSettings').mockResolvedValue(emptyCasino)
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([])
    const updateSpy = vi
      .spyOn(client, 'updateEconomySettings')
      .mockResolvedValue({ ...emptySettings, daily_bonus_enabled: false, daily_base_amount: 100 })
    render(<EconomyPage />)

    expect(await screen.findByText(/Ежедневный бонус — \/daily/)).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Включено'))
    fireEvent.change(screen.getByLabelText(/База \(день 1\)/), { target: { value: '100' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ daily_bonus_enabled: false, daily_base_amount: 100 }),
      ),
    )
  })

  it('shows an error when loading fails', async () => {
    vi.spyOn(client, 'fetchEconomySettings').mockRejectedValue(new Error('fail'))
    mockCasino()
    vi.spyOn(client, 'fetchEconomyTop').mockResolvedValue([])
    render(<EconomyPage />)
    expect(await screen.findByText('Не удалось загрузить настройки модуля «Экономика»')).toBeInTheDocument()
  })
})
