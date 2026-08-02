import { fireEvent, screen, waitFor } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
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

const emptyQuote: client.QuoteSettings = {
  enabled: true,
  delete_trigger: false,
  min_length: 0,
}

function mockExtras() {
  vi.spyOn(client, 'fetchWordleSettings').mockResolvedValue(emptyWordle)
  vi.spyOn(client, 'fetchQuoteSettings').mockResolvedValue(emptyQuote)
  vi.spyOn(client, 'fetchAutoReactions').mockResolvedValue({ enabled: false, rules: [] })
  vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
}

describe('FunPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the module toggle and roulette card', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockExtras()
    renderWithLanguage(<FunPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getAllByText(/Русская рулетка/).length).toBeGreaterThan(0)
  })

  it('toggles enabled and saves settings', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockExtras()
    vi.spyOn(client, 'updateWordleSettings').mockResolvedValue(emptyWordle)
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue({ ...emptySettings, enabled: true })

    renderWithLanguage(<FunPage />)
    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить развлечения' }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true })))
    expect(await screen.findByText('Сохранено')).toBeInTheDocument()
  })

  it('updates timeout and cooldown fields before saving', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockExtras()
    vi.spyOn(client, 'updateWordleSettings').mockResolvedValue(emptyWordle)
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue(emptySettings)
    renderWithLanguage(<FunPage />)

    fireEvent.change(await screen.findByLabelText(/Таймаут проигравшему/), { target: { value: '10' } })
    fireEvent.change(screen.getByLabelText(/Кулдаун на игрока/), { target: { value: '120' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить развлечения' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ roulette_timeout_minutes: 10, roulette_cooldown_sec: 120 }),
      ),
    )
  })

  it('renders the auto-emoji tab and saves its settings', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockExtras()
    vi.spyOn(client, 'updateWordleSettings').mockResolvedValue(emptyWordle)
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue(emptySettings)
    renderWithLanguage(<FunPage />, { initialEntries: ['/fun?tab=autoEmoji'] })

    expect(await screen.findByText('Случайные реакции')).toBeInTheDocument()
    fireEvent.click(screen.getAllByLabelText('Выключено')[0])
    fireEvent.change(screen.getByLabelText(/Шанс на сообщение/), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить случайные' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ auto_emoji_enabled: true, auto_emoji_chance_percent: 10 }),
      ),
    )
  })

  it('renders the wordle card and saves its settings', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockExtras()
    vi.spyOn(client, 'updateFunSettings').mockResolvedValue(emptySettings)
    const wordleSpy = vi
      .spyOn(client, 'updateWordleSettings')
      .mockResolvedValue({ enabled: true, channel_id: '555', announce_time: '18:30' })
    renderWithLanguage(<FunPage />, { initialEntries: ['/fun?tab=wordle'] })

    expect(await screen.findByRole('heading', { name: /Вордл/ })).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/Вордл выключен|Wordle disabled|выключен/i))
    fireEvent.change(screen.getByLabelText(/ID канала|канала для анонсов|Channel/i), {
      target: { value: '555' },
    })
    fireEvent.change(screen.getByLabelText(/Время|announce|Announce/i), { target: { value: '18:30' } })
    fireEvent.click(screen.getByRole('button', { name: /Сохранить Вордл|Save Wordle|Сохранить/i }))

    await waitFor(() =>
      expect(wordleSpy).toHaveBeenCalledWith(
        expect.objectContaining({ enabled: true, channel_id: '555', announce_time: '18:30' }),
      ),
    )
  })

  it('saves fun without requiring wordle save', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    mockExtras()
    const updateSpy = vi.spyOn(client, 'updateFunSettings').mockResolvedValue({ ...emptySettings, enabled: true })
    const wordleSpy = vi.spyOn(client, 'updateWordleSettings')
    renderWithLanguage(<FunPage />)

    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить развлечения' }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalled())
    expect(wordleSpy).not.toHaveBeenCalled()
  })

  it('loads fun even when wordle fails', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockResolvedValue(emptySettings)
    vi.spyOn(client, 'fetchWordleSettings').mockRejectedValue(new Error('fail'))
    vi.spyOn(client, 'fetchQuoteSettings').mockResolvedValue(emptyQuote)
    renderWithLanguage(<FunPage />)
    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getAllByText(/Русская рулетка/).length).toBeGreaterThan(0)
  })

  it('shows an error when loading fails', async () => {
    vi.spyOn(client, 'fetchFunSettings').mockRejectedValue(new Error('fail'))
    mockExtras()
    renderWithLanguage(<FunPage />)
    expect(await screen.findByText('Не удалось загрузить настройки модуля «Развлечения»')).toBeInTheDocument()
  })
})
