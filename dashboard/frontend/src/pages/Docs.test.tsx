import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { LanguageProvider } from '../context/LanguageContext'
import { DocsPage } from './Docs'

function renderAt(path: string) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({}) }))

  return render(
    <MemoryRouter initialEntries={[path]}>
      <LanguageProvider>
        <AuthProvider>
          <Routes>
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/docs/:sectionId" element={<DocsPage />} />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </MemoryRouter>,
  )
}

describe('DocsPage', () => {
  it('renders the default section and sidebar groups', async () => {
    renderAt('/docs')

    expect(await screen.findByRole('heading', { level: 1, name: 'Введение' })).toBeInTheDocument()
    expect(screen.getByText('Общее')).toBeInTheDocument()
    expect(screen.getByText('Модули')).toBeInTheDocument()
    expect(screen.getByText('Справка')).toBeInTheDocument()
  })

  it('navigates to a section via the sidebar', async () => {
    renderAt('/docs')
    await screen.findByRole('heading', { level: 1, name: 'Введение' })

    const sidebarNav = screen.getByRole('navigation', { name: 'Разделы документации' })
    fireEvent.click(within(sidebarNav).getByRole('link', { name: 'Начало работы' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Начало работы' })).toBeInTheDocument()
  })

  it('opens the search palette on Ctrl+K and jumps to a result', async () => {
    renderAt('/docs')
    await screen.findByRole('heading', { level: 1, name: 'Введение' })

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    expect(await screen.findByRole('dialog')).toBeInTheDocument()

    const input = screen.getByPlaceholderText('Название раздела…')
    fireEvent.change(input, { target: { value: 'Начало работы' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Начало работы' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Начало работы' })).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders a pager link to the next section', async () => {
    renderAt('/docs')
    await screen.findByRole('heading', { level: 1, name: 'Введение' })

    const pager = screen.getByRole('navigation', { name: 'Пейджер' })
    fireEvent.click(within(pager).getByRole('link', { name: /Начало работы/ }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Начало работы' })).toBeInTheDocument()
  })

  it('switches docs content to English when language is en', async () => {
    renderAt('/docs')
    await screen.findByRole('heading', { level: 1, name: 'Введение' })

    fireEvent.click(screen.getByRole('button', { name: 'English' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Introduction' })).toBeInTheDocument()
    expect(screen.getByText('General')).toBeInTheDocument()
    expect(screen.getByText('Modules')).toBeInTheDocument()
    expect(screen.getByText('Reference')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Copy page' })).toBeInTheDocument()
  })
})
