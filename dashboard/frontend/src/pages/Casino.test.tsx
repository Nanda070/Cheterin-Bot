import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { CasinoPage } from './Casino'

const emptySettings: client.CasinoSettings = {
  enabled: false,
  house_edge_percent: 5,
  cooldown_sec: 5,
  min_bet: 10,
  max_bet: 5000,
  loss_roles: [],
}

const emptyLeaderboard: client.CasinoLeaderboardResponse = {
  entries: [],
  total: 0,
  page: 1,
  page_size: 50,
}

describe('CasinoPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders settings and an empty leaderboard', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptySettings)
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
    render(<CasinoPage />)

    expect(await screen.findByText('Выключено')).toBeInTheDocument()
    expect(screen.getByText('Настройки игры')).toBeInTheDocument()
    expect(await screen.findByText('Таблица пуста.')).toBeInTheDocument()
    expect(screen.getByText(/Лидерборд \(всего записей: 0\)/)).toBeInTheDocument()
  })

  it('saves updated settings', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptySettings)
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
    const updateSpy = vi
      .spyOn(client, 'updateCasinoSettings')
      .mockResolvedValue({ ...emptySettings, enabled: true, house_edge_percent: 10 })
    render(<CasinoPage />)

    fireEvent.click(await screen.findByLabelText('Выключено'))
    fireEvent.change(screen.getByLabelText(/Преимущество казино/), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true, house_edge_percent: 10 })),
    )
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('adds and removes a loss-role rule', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptySettings)
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
    const updateSpy = vi.spyOn(client, 'updateCasinoSettings').mockImplementation(async (s) => s)
    const { container } = render(<CasinoPage />)

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
    await screen.findByText('Сохранено.')

    const removeButton = container.querySelector('input[placeholder="ID роли"]')!.closest('div')!.querySelector('button')!
    fireEvent.click(removeButton)
    expect(screen.queryByPlaceholderText('ID роли')).not.toBeInTheDocument()
  })

  it('strips non-digit characters from the role id field', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptySettings)
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
    render(<CasinoPage />)

    fireEvent.click(await screen.findByRole('button', { name: /Добавить роль/ }))
    const roleInput = screen.getByPlaceholderText('ID роли') as HTMLInputElement
    fireEvent.change(roleInput, { target: { value: '12a3b' } })

    expect(roleInput.value).toBe('123')
  })

  it('renders leaderboard entries and switches mode/type/page', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptySettings)
    const lbSpy = vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue({
      entries: [
        { user_id: '1', username: 'Rich', avatar: null, slots_losses: 2, slots_wins: 5, bj_losses: 1, bj_wins: 3 },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    })
    render(<CasinoPage />)

    expect(await screen.findByText('Rich')).toBeInTheDocument()
    // Дефолтный режим — «Проигрыши»: slots_losses(2) + bj_losses(1) = 3
    expect(screen.getByText(/Всего: 3 ❌/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Блэкджек/ }))
    await waitFor(() => expect(lbSpy).toHaveBeenLastCalledWith('bj', 'losses', 1))

    fireEvent.click(screen.getByRole('button', { name: /Победы/ }))
    await waitFor(() => expect(lbSpy).toHaveBeenLastCalledWith('bj', 'wins', 1))
  })

  it('paginates the leaderboard forward and back', async () => {
    vi.spyOn(client, 'fetchCasinoSettings').mockResolvedValue(emptySettings)
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
    render(<CasinoPage />)

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
    vi.spyOn(client, 'fetchCasinoLeaderboard').mockResolvedValue(emptyLeaderboard)
    render(<CasinoPage />)
    expect(await screen.findByText('Не удалось загрузить настройки казино')).toBeInTheDocument()
  })
})
