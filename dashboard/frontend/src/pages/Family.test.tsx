import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FamilyPage } from './Family'

const emptySettings: client.FamilySettings = {
  enabled: false,
  roster: { list_channel_id: '', target_roles: [] },
  applications: {
    application_channel_id: '',
    log_channel_id: '',
    staff_role_ids: [],
    ticket_manager_role_id: '',
    notify_role_id: '',
    ticket_active_role_id: '',
    approve_role_ids: [],
    yes_emoji_id: '',
    no_emoji_id: '',
    thread_archive_minutes: 10080,
  },
  birthdays: { channel_id: '', list_channel_id: '' },
}

function mockBaseFetches(settings: client.FamilySettings = emptySettings) {
  vi.spyOn(client, 'fetchFamilySettings').mockResolvedValue(settings)
  vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
  vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
  vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])
}

describe('FamilyPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the module toggle and tabs', async () => {
    mockBaseFetches()
    renderWithLanguage(<FamilyPage />)

    expect(await screen.findByText('Модуль выключен')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Настройки' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ростер' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Заявки' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Дни рождения' })).toBeInTheDocument()
  })

  it('toggles enabled and saves settings', async () => {
    mockBaseFetches()
    const updateSpy = vi.spyOn(client, 'updateFamilySettings').mockResolvedValue({ ...emptySettings, enabled: true })

    renderWithLanguage(<FamilyPage />)
    fireEvent.click(await screen.findByLabelText('Модуль выключен'))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ enabled: true })))
    expect(await screen.findByText('Сохранено')).toBeInTheDocument()
  })

  it('adds a target role row in roster settings', async () => {
    mockBaseFetches()
    renderWithLanguage(<FamilyPage />)

    fireEvent.click(await screen.findByText('Добавить роль'))

    expect(screen.getByPlaceholderText('Название группы')).toBeInTheDocument()
  })

  it('shows roster groups on the roster tab', async () => {
    mockBaseFetches()
    vi.spyOn(client, 'fetchFamilyRoster').mockResolvedValue({
      groups: [
        { label: 'Верхушка', role_id: '7', role_found: true, members: [{ id: '20', display: 'Alice' }] },
      ],
    })

    renderWithLanguage(<FamilyPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Ростер' }))

    expect(await screen.findByText('Верхушка')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
  })

  it('lists tickets and approves one', async () => {
    mockBaseFetches()
    vi.spyOn(client, 'fetchFamilyTickets').mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 25,
      entries: [
        {
          user_id: '20',
          display: 'Applicant',
          status: 'open',
          nickname: 'Nick',
          game_level: '99',
          faction_pref: 'Gov',
          online_timezone: 'MSK',
          real_name: 'Ivan',
          real_age: '20',
          about_text: 'about',
          why_join: 'why',
          inviter_nickname: null,
          created_at: '01.01.2026 00:00 UTC',
          handled_by: null,
          thread_id: '800',
        },
      ],
    })
    const decideSpy = vi.spyOn(client, 'decideFamilyTicket').mockResolvedValue()

    renderWithLanguage(<FamilyPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Заявки' }))

    await screen.findByText('Nick · Applicant')
    fireEvent.click(screen.getByText('Принять'))

    await waitFor(() => expect(decideSpy).toHaveBeenCalledWith('20', 'approve'))
  })

  it('lists birthdays and adds a new one after picking a member', async () => {
    mockBaseFetches()
    vi.spyOn(client, 'fetchFamilyBirthdays').mockResolvedValue({
      entries: [{ user_id: '20', display: 'Alice', day: 5, month: 1, date_display: '05.01' }],
    })
    vi.spyOn(client, 'fetchMembers').mockResolvedValue({
      total: 1,
      page: 1,
      page_size: 20,
      members: [{ id: '30', username: 'bob', display_name: 'Bob', avatar: null, role_count: 0, joined_at: null, is_bot: false }],
    })
    const setSpy = vi.spyOn(client, 'setFamilyBirthday').mockResolvedValue({ date_display: '06.02' })

    renderWithLanguage(<FamilyPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Дни рождения' }))

    await screen.findByText('05.01')

    fireEvent.change(screen.getByPlaceholderText('Поиск участника…'), { target: { value: 'bob' } })
    fireEvent.click(await screen.findByText('Bob'))
    fireEvent.change(screen.getByPlaceholderText('дд.мм или 1 января'), { target: { value: '06.02' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(setSpy).toHaveBeenCalledWith('30', '06.02'))
  })
})
