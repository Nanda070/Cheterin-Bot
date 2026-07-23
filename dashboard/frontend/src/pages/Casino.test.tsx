import { fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { CasinoPage } from './Casino'

const emptySettings: client.CasinoSettings = {
  enabled: false,
  house_edge_percent: 5,
  cooldown_sec: 5,
  min_bet: 10,
  max_bet: 5000,
  loss_roles: [],
}

const emptyEconomy: client.EconomySettings = {
  enabled: true,
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
  weekly_report_enabled: false,
  weekly_report_channel_id: '',
  weekly_report_days: 7,
}

const emptyLeaderboard: client.CasinoLeaderboardResponse = {
  entries: [],
  total: 0,
  page: 1,
  page_size: 50,
}

describe('CasinoPage', () => {
  afterEach(() => vi.restoreAllMocks())

  function mockBase(casino: client.CasinoSettings = emptySettings) {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(casino)
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptyEconomy)
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
  }

  it('renders settings and roulette bets card', async () => {
    mockBase()
    renderWithLanguage(<CasinoPage />)

    expect(await screen.findByText('Выключено')).toBeInTheDocument()
    expect(screen.getByText('Настройки игры')).toBeInTheDocument()
    expect(await screen.findByText('Ставки в русской рулетке')).toBeInTheDocument()
    expect(await screen.findByLabelText(/Макс\. ставка в рулетке/)).toBeInTheDocument()
    expect(screen.queryByText('Таблица пуста.')).not.toBeInTheDocument()
  })

  it('still renders casino settings when economy fails', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptySettings)
    vi.spyOn(client, 'fetchEconomySettings').mockRejectedValue(new Error('fail'))
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
    renderWithLanguage(<CasinoPage />)

    expect(await screen.findByText('Выключено')).toBeInTheDocument()
    expect(await screen.findByText(/Не удалось загрузить ставки рулетки/)).toBeInTheDocument()
  })

  it('shows leaderboard on its tab', async () => {
    mockBase()
    renderWithLanguage(<CasinoPage />)

    fireEvent.click(await screen.findByRole('button', { name: 'Лидерборд' }))
    expect(await screen.findByText('Таблица пуста.')).toBeInTheDocument()
    expect(screen.getByText(/Лидерборд \(всего записей: 0\)/)).toBeInTheDocument()
  })

  it('saves casino then refreshes economy before writing roulette fields', async () => {
    mockBase()
    const updateCasinoSpy = vi
      .spyOn(client, 'updateCasinoSettings')
      .mockResolvedValue({ ...emptySettings, enabled: true, house_edge_percent: 10 })
    const fetchEconomySpy = vi.spyOn(client, 'fetchEconomySettings')
    const updateEconomySpy = vi
      .spyOn(client, 'updateEconomySettings')
      .mockResolvedValue({ ...emptyEconomy, roulette_max_bet: 250, shop_items: [{ id: '1', type: 'role', role_id: '9', color_hex: '', title_text: '', price: 1, name: 'VIP' }] })

    renderWithLanguage(<CasinoPage />)

    fireEvent.click(await screen.findByLabelText('Выключено'))
    fireEvent.change(await screen.findByLabelText(/Преимущество казино/), { target: { value: '10' } })
    fireEvent.change(await screen.findByLabelText(/Макс\. ставка в рулетке/), { target: { value: '250' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateCasinoSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true, house_edge_percent: 10 })),
    )
    await waitFor(() => expect(fetchEconomySpy.mock.calls.length).toBeGreaterThanOrEqual(2))
    await waitFor(() =>
      expect(updateEconomySpy).toHaveBeenCalledWith(
        expect.objectContaining({ roulette_max_bet: 250, roulette_bets_enabled: true }),
      ),
    )
    expect(await screen.findByText('Сохранено')).toBeInTheDocument()
  })

  it('adds and removes a loss-role rule', async () => {
    mockBase()
    const updateSpy = vi.spyOn(client, 'updateCasinoSettings').mockImplementation(async (s) => s)
    vi.spyOn(client, 'updateEconomySettings').mockResolvedValue(emptyEconomy)
    const { container } = renderWithLanguage(<CasinoPage />)

    fireEvent.click(await screen.findByRole('button', { name: /Добавить роль/ }))
    fireEvent.change(screen.getByPlaceholderText('ID роли'), { target: { value: '777' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          loss_roles: [expect.objectContaining({ role_id: '777', game: 'total', threshold: 10 })],
        }),
      ),
    )
    await screen.findByText('Сохранено')

    const removeButton = container.querySelector('input[placeholder="ID роли"]')!.closest('div')!.querySelector('button')!
    fireEvent.click(removeButton)
    expect(screen.queryByPlaceholderText('ID роли')).not.toBeInTheDocument()
  })

  it('strips non-digit characters from the role id field', async () => {
    mockBase()
    renderWithLanguage(<CasinoPage />)

    fireEvent.click(await screen.findByRole('button', { name: /Добавить роль/ }))
    const roleInput = screen.getByPlaceholderText('ID роли') as HTMLInputElement
    fireEvent.change(roleInput, { target: { value: '12a3b' } })

    expect(roleInput.value).toBe('123')
  })

  it('renders leaderboard entries and switches mode/type/page', async () => {
    mockBase()
    const lbSpy = vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue({
      entries: [
        { user_id: '1', username: 'Rich', avatar: null, slots_losses: 2, slots_wins: 5, bj_losses: 1, bj_wins: 3 },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    })
    renderWithLanguage(<CasinoPage />)

    fireEvent.click(await screen.findByRole('button', { name: 'Лидерборд' }))
    expect(await screen.findByText('Rich')).toBeInTheDocument()
    expect(screen.getByText(/Всего: 3 ❌/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Блэкджек/ }))
    await waitFor(() => expect(lbSpy).toHaveBeenLastCalledWith('bj', 'losses', 1))

    fireEvent.click(screen.getByRole('button', { name: /Победы/ }))
    await waitFor(() => expect(lbSpy).toHaveBeenLastCalledWith('bj', 'wins', 1))
  })

  it('paginates the leaderboard forward and back', async () => {
    mockBase()
    const fullPage = Array.from({ length: 50 }, (_, i) => ({
      user_id: String(i),
      username: `Player${i}`,
      avatar: null,
      slots_losses: 0,
      slots_wins: 0,
      bj_losses: 0,
      bj_wins: 0,
    }))
    const lbSpy = vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue({
      entries: fullPage,
      total: 60,
      page: 1,
      page_size: 50,
    })
    renderWithLanguage(<CasinoPage />)

    fireEvent.click(await screen.findByRole('button', { name: 'Лидерборд' }))
    await screen.findByText('Player0')
    const nextButton = screen.getByRole('button', { name: 'Вперёд' })
    expect(nextButton).not.toBeDisabled()

    fireEvent.click(nextButton)
    await waitFor(() => expect(lbSpy).toHaveBeenLastCalledWith('total', 'losses', 2))

    fireEvent.click(screen.getByRole('button', { name: 'Назад' }))
    await waitFor(() => expect(lbSpy).toHaveBeenLastCalledWith('total', 'losses', 1))
  })

  it('shows an error when loading settings fails', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockRejectedValue(new Error('fail'))
    vi.spyOn(client, 'fetchEconomySettings').mockResolvedValue(emptyEconomy)
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
    renderWithLanguage(<CasinoPage />)
    expect(await screen.findByText('Не удалось загрузить настройки казино')).toBeInTheDocument()
  })
})
