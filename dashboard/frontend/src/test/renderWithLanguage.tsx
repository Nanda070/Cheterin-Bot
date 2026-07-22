import { render, type RenderOptions } from '@testing-library/react'
import type { ReactElement } from 'react'
import { LanguageProvider } from '../context/LanguageContext'

export function renderWithLanguage(ui: ReactElement, options?: RenderOptions) {
  return render(<LanguageProvider>{ui}</LanguageProvider>, options)
}
