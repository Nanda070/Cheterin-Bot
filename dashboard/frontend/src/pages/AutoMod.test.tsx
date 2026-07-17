import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AutoModPage } from './AutoMod'

function makeFilter(overrides: Partial<client.AutomodFilter> = {}): client.AutomodFilter {
  return {
    label: 'Ссылки',
    description: 'Нежелательные ссылки',
    enabled: false,
    delete_message: true,
    punishment: 'warn',
    duration_minutes: 0,
    notify_member: false,
    notify_channel_id: '',
    notify_template: 'Привет {{member}}! Вы получили предупреждение: {{reason}}.',
    whitelist_domains: [],
    ...overrides,
  }
}

const FILTER_KEYS = ['links', 'invites', 'scam_links', 'bad_words', 'repeated_text', 'caps_lock', 'emoji_spam', 'mentions', 'zalgo']

function baseSettings(overrides: Partial<client.AutomodSettings> = {}): client.AutomodSettings {
  const filters: Record<string, client.AutomodFilter> = {}
  for (const key of FILTER_KEYS) {
    filters[key] = makeFilter({ label: key, description: `desc-${key}` })
  }
  return {
    enabled: false,
    filters,
    escalation: [],
    manual_warn_duration_minutes: 43200,
    ...overrides,
  }
}

function mockBaseFetches(settings: client.AutomodSettings = baseSettings()) {
  vi.spyOn(client, 'fetchAutomod').mockResolvedValue(settings)
  vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
}

describe('AutoModPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders all 9 filter cards, disabled by default', async () => {
    mockBaseFetches()
    render(<AutoModPage />)

    expect(await screen.findByText('Автомодерация')).toBeInTheDocument()
    for (const key of FILTER_KEYS) {
      expect(screen.getByText(key)).toBeInTheDocument()
    }
    const moduleToggle = screen.getAllByRole('switch')[0]
    expect(moduleToggle).toHaveAttribute('aria-checked', 'false')
  })

  it('toggles the whole module on', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateAutomodEnabled').mockResolvedValue(baseSettings({ enabled: true }))

    render(<AutoModPage />)
    await screen.findByText('Автомодерация')

    fireEvent.click(screen.getAllByRole('switch')[0])
    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(true))
  })

  it('toggles a single filter on', async () => {
    mockBaseFetches()
    const updateFilterSpy = vi.spyOn(client, 'updateAutomodFilter').mockResolvedValue(makeFilter({ enabled: true }))

    render(<AutoModPage />)
    await screen.findByText('links')

    // switches[0] = module toggle, switches[1] = first filter card (links)
    fireEvent.click(screen.getAllByRole('switch')[1])
    await waitFor(() => expect(updateFilterSpy).toHaveBeenCalledWith('links', { enabled: true }))
  })

  it('opens filter settings and saves changes', async () => {
    mockBaseFetches()
    const updateFilterSpy = vi.spyOn(client, 'updateAutomodFilter').mockResolvedValue(makeFilter())

    render(<AutoModPage />)
    await screen.findByText('links')

    fireEvent.click(screen.getByRole('button', { name: 'Настройки фильтра links' }))
    expect(await screen.findByText('Удалять сообщение с нарушением')).toBeInTheDocument()

    const saveButtons = screen.getAllByRole('button', { name: 'Сохранить' })
    fireEvent.click(saveButtons[saveButtons.length - 1])
    await waitFor(() => expect(updateFilterSpy).toHaveBeenCalled())
  })

  it('adds an escalation rule', async () => {
    mockBaseFetches()
    const createSpy = vi.spyOn(client, 'createEscalationRule').mockResolvedValue({
      id: '1',
      count: 3,
      action: 'mute',
      duration_minutes: 1440,
    })

    render(<AutoModPage />)
    await screen.findByText('Эскалация по количеству предупреждений')

    fireEvent.click(screen.getByRole('button', { name: /Добавить порог/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Добавить' }))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith({ count: 3, action: 'mute', duration_minutes: 1440 }),
    )
  })

  it('shows existing escalation rules and deletes one', async () => {
    mockBaseFetches(baseSettings({ escalation: [{ id: '9', count: 5, action: 'kick', duration_minutes: 0 }] }))
    const deleteSpy = vi.spyOn(client, 'deleteEscalationRule').mockResolvedValue()

    render(<AutoModPage />)
    expect(await screen.findByText(/5 предупреждений → Кик/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Удалить порог 5' }))
    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('9'))
  })

  it('saves the manual warn duration', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateManualWarnDuration').mockResolvedValue(baseSettings())

    render(<AutoModPage />)
    await screen.findByText('Срок ручных предупреждений')

    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))
    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(43200))
  })
})
