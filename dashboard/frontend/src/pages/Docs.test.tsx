import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { DocsPage } from './Docs'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/docs/:sectionId" element={<DocsPage />} />
      </Routes>
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
})
