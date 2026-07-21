import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { BunkerPage } from './Bunker'

const emptySettings: client.BunkerSettings = {
  enabled: false,
  default_min_players: 4,
  default_max_players: 12,
  default_discussion_timer_sec: 180,
  default_vote_timer_sec: 90,
  default_unique_cards: true,
  log_channel_id: '',
}

const baseGameSummary: client.BunkerGameSummary = {
  id: 1,
  channel_id: '500',
  channel_name: 'general',
  status: 'active',
  phase: 'discussion',
  round_number: 1,
  bunker_capacity: 2,
  unique_cards: true,
  player_count: 2,
  alive_count: 2,
  created_at: '2026-01-01T00:00:00Z',
}

const mockPools: client.BunkerCardPools = {
  genders: ['Мужской', 'Женский'],
  ages: [{ key: 'adult', label: 'Взрослый (35-59 лет)' }],
  body_types: [
    {
      key: 'strong', name: 'Крепкое', agility: 'Обычная', stamina: 'Высокая', strength: 'Высокая',
      disease_note: 'Обычная', food_requirement: 'Обычная', heat_tolerance: 'Обычная', cold_tolerance: 'Обычная',
      reproduction: 'Возможно',
    },
  ],
  professions: [
    { id: 1, name: 'Пожарный', category: 'МЧС' },
    { id: 2, name: 'Врач', category: 'Медицина' },
  ],
  profession_experience_levels: [{ level: 'Эксперт', duration: 'от 10 лет', has_ability: true }],
  hobbies: [{ id: 1, name: 'Рыбалка', category: 'Хобби' }],
  hobby_experience_levels: [{ level: 'Мастер (гуру)', duration: 'от 5 лет' }],
  health_severities: ['Здоров', 'Лёгкая'],
  health_diseases: [{ id: 1, name: 'Клаустрофобия', category: 'Психологические заболевания' }],
  phobias: [{ id: 1, name: 'Без фобий', type: 'Нет' }],
  backpack_items: [{ id: 1, name: 'Нож', category: 'Инструменты' }],
  large_items: [{ id: 1, name: 'Генератор', category: 'Оборудование' }],
  traits: [{ trait: 'Альтруист', category: 'Моральная', behavior_example: '...', possible_bunker_behavior: '...' }],
  additional_info: [{ id: 1, name: 'Бывший спасатель', category: 'Жизненный опыт' }],
  special_abilities: [
    { id: 1, name: 'Джокер', category: 'Защита', effect: 'эффект 1' },
    { id: 2, name: 'Сейф', category: 'Защита', effect: 'эффект 2' },
  ],
}

function mockBaseFetches(settings: client.BunkerSettings = emptySettings) {
  vi.spyOn(client, 'fetchBunkerSettings').mockResolvedValue(settings)
  vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
}

describe('BunkerPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the module toggle and tabs', async () => {
    mockBaseFetches()
    render(<BunkerPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Настройки' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Активные игры' })).toBeInTheDocument()
  })

  it('toggles enabled and saves settings', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateBunkerSettings').mockResolvedValue({ ...emptySettings, enabled: true })

    render(<BunkerPage />)
    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true })))
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('updates a timer field before saving', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateBunkerSettings').mockResolvedValue(emptySettings)
    render(<BunkerPage />)

    const input = await screen.findByLabelText(/^Голосование за исключение/)
    fireEvent.change(input, { target: { value: '120' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ default_vote_timer_sec: 120 })),
    )
  })

  it('toggles the default unique-cards setting and saves', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateBunkerSettings').mockResolvedValue({ ...emptySettings, default_unique_cards: false })

    render(<BunkerPage />)
    fireEvent.click(await screen.findByLabelText('Без повторов (колодой)'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ default_unique_cards: false })),
    )
  })

  it('lists active games with unique-cards status', async () => {
    mockBaseFetches()
    vi.spyOn(client, 'fetchBunkerGames').mockResolvedValue([{ ...baseGameSummary, round_number: 2, player_count: 8, alive_count: 6 }])

    render(<BunkerPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Активные игры' }))

    expect(await screen.findByText('Игра #1 · general')).toBeInTheDocument()
    expect(screen.getByText(/раунд 2/)).toBeInTheDocument()
    expect(screen.getByText(/вместимость 2/)).toBeInTheDocument()
    expect(screen.getByText(/карточки без повторов/)).toBeInTheDocument()
  })

  it('opens a game detail with roster and ability announcements, and applies one', async () => {
    mockBaseFetches()
    vi.spyOn(client, 'fetchBunkerGames').mockResolvedValue([baseGameSummary])
    vi.spyOn(client, 'fetchBunkerCardPools').mockResolvedValue(mockPools)
    vi.spyOn(client, 'fetchBunkerGameDetail').mockResolvedValue({
      game: baseGameSummary,
      players: [
        {
          user_id: '20',
          display_name: 'Alice',
          alive: true,
          character: { profession: { name: 'Врач', category: 'Медицина', experience_level: 'Эксперт', has_ability: true } },
          revealed_fields: ['profession'],
        },
      ],
      ability_announcements: [
        {
          id: 5,
          round_number: 1,
          player_user_id: '20',
          player_display_name: 'Alice',
          card_index: 1,
          card_name: 'Джокер',
          target_user_id: null,
          target_display_name: null,
          note: 'применить на себя',
          applied: false,
          created_at: '2026-01-01T00:00:00Z',
        },
      ],
    })
    const applySpy = vi.spyOn(client, 'applyBunkerAbility').mockResolvedValue()

    render(<BunkerPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Активные игры' }))
    fireEvent.click(await screen.findByText('Игра #1 · general'))

    expect(await screen.findAllByText('Alice')).not.toHaveLength(0)
    expect(screen.getByText(/«Джокер»/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Применить' }))
    await waitFor(() => expect(applySpy).toHaveBeenCalledWith(1, 5))
  })

  it('opens the typed character editor and saves a changed profession', async () => {
    mockBaseFetches()
    vi.spyOn(client, 'fetchBunkerGames').mockResolvedValue([baseGameSummary])
    vi.spyOn(client, 'fetchBunkerCardPools').mockResolvedValue(mockPools)
    vi.spyOn(client, 'fetchBunkerGameDetail').mockResolvedValue({
      game: baseGameSummary,
      players: [
        {
          user_id: '20',
          display_name: 'Alice',
          alive: true,
          character: { profession: { name: 'Пожарный', category: 'МЧС', experience_level: 'Эксперт', has_ability: true } },
          revealed_fields: [],
        },
      ],
      ability_announcements: [],
    })
    const patchSpy = vi.spyOn(client, 'patchBunkerPlayerCharacter').mockResolvedValue({ character: {} })

    render(<BunkerPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Активные игры' }))
    fireEvent.click(await screen.findByText('Игра #1 · general'))
    fireEvent.click(await screen.findByRole('button', { name: 'Редактировать' }))

    fireEvent.click(await screen.findByRole('button', { name: 'Пожарный' }))
    fireEvent.click(await screen.findByRole('option', { name: 'Врач' }))

    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(patchSpy).toHaveBeenCalled())
    const [gameId, userId, character] = patchSpy.mock.calls[0]
    expect(gameId).toBe(1)
    expect(userId).toBe('20')
    expect(character.profession?.name).toBe('Врач')
  })
})
