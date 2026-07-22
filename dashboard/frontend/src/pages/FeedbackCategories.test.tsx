import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackCategoriesPage } from './FeedbackCategories'

const sampleCategory: client.FeedbackCategorySpec = {
  key: 'players',
  title: 'Жалоба на участника',
  button_label: 'Жалоба на участника',
  channel_id: '500',
  case_prefix: 'PR',
  case_title: 'Жалоба на участника',
  thread_name: 'player-report',
  review_role_ids: ['111'],
  approved_text: 'Участник наказан.',
  denied_text: 'Жалоба отклонена.',
  modal_title: 'Жалоба на участника',
  fields: [{ key: 'offender', label: 'Ник участника', style: 'short', required: true, max_length: 120 }],
  mini_summary_key: 'offender',
}

describe('FeedbackCategoriesPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists existing categories', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([sampleCategory])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '111', name: 'Reviewers', color: '#000000', position: 1 }])

    renderWithLanguage(<FeedbackCategoriesPage />)

    expect(await screen.findByText('Жалоба на участника')).toBeInTheDocument()
    expect(screen.getByText((_, element) => element?.tagName === 'P' && !!element.textContent?.startsWith('PR'))).toBeInTheDocument()
  })

  it('creates a new category', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '111', name: 'Reviewers', color: '#000000', position: 1 }])
    const createSpy = vi.spyOn(client, 'createFeedbackCategory').mockResolvedValue(sampleCategory)

    renderWithLanguage(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByText('Создать категорию'))
    fireEvent.click(screen.getByText('Создать категорию'))

    await waitFor(() => screen.getByLabelText('Ключ'))
    fireEvent.change(screen.getByLabelText('Ключ'), { target: { value: 'players' } })
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Текст кнопки'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Заголовок дела'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Заголовок формы'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Имя треда'), { target: { value: 'player-report' } })
    fireEvent.change(screen.getByLabelText('Префикс дела'), { target: { value: 'PR' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Текст при принятии'), { target: { value: 'Участник наказан.' } })
    fireEvent.change(screen.getByLabelText('Текст при отклонении'), { target: { value: 'Жалоба отклонена.' } })
    fireEvent.change(screen.getByPlaceholderText('Ключ поля'), { target: { value: 'offender' } })
    fireEvent.change(screen.getByPlaceholderText('Название поля'), { target: { value: 'Ник участника' } })

    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(createSpy).toHaveBeenCalled())
  })

  it('deletes a category after confirmation', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([sampleCategory])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const deleteSpy = vi.spyOn(client, 'deleteFeedbackCategory').mockResolvedValue(undefined)

    renderWithLanguage(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByText('Удалить'))
    fireEvent.click(screen.getByText('Удалить'))
    fireEvent.click(screen.getByText('Удалить категорию'))

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('players'))
  })

  it('opens the create form pre-filled with the default category template', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderWithLanguage(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByText('Дефолтный шаблон'))
    fireEvent.click(screen.getByText('Дефолтный шаблон'))

    await waitFor(() => screen.getByLabelText('Ключ'))
    expect((screen.getByLabelText('Ключ') as HTMLInputElement).value).toBe('players')
    expect((screen.getByLabelText('Префикс дела') as HTMLInputElement).value).toBe('PR')
    expect((screen.getByLabelText('Имя треда') as HTMLInputElement).value).toBe('player-report')
    expect((screen.getByLabelText('Название') as HTMLInputElement).value).toBe('Жалоба на участника')
  })

  it('prefills the default template in the current UI language', async () => {
    const store: Record<string, string> = { chetbot_ui_lang: 'en' }
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = value
      },
      removeItem: (key: string) => {
        delete store[key]
      },
    })
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderWithLanguage(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByText('Default template'))
    fireEvent.click(screen.getByText('Default template'))

    await waitFor(() => screen.getByLabelText('Title'))
    expect((screen.getByLabelText('Title') as HTMLInputElement).value).toBe('Member report')
    vi.unstubAllGlobals()
  })

  it('publishes the panel to the selected channel', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const publishSpy = vi.spyOn(client, 'publishFeedbackPanel').mockResolvedValue({ ok: true, message_id: '999' })

    renderWithLanguage(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByRole('button', { name: 'Опубликовать' }))
    fireEvent.click(screen.getByRole('button', { name: 'Опубликовать' }))

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'reports' }))

    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Опубликовать' }))

    await waitFor(() => expect(publishSpy).toHaveBeenCalledWith('500'))
  })
})
