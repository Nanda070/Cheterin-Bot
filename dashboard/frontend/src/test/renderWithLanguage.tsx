import { render, type RenderOptions } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { LanguageProvider } from '../context/LanguageContext'

export function renderWithLanguage(
  ui: ReactElement,
  options?: RenderOptions & { initialEntries?: string[] },
) {
  const { initialEntries = ['/'], ...renderOptions } = options ?? {}
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <LanguageProvider>{ui}</LanguageProvider>
    </MemoryRouter>,
    renderOptions,
  )
}
