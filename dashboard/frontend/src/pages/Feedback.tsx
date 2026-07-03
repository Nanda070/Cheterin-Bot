import { useState } from 'react'
import { FeedbackCasesPage } from './FeedbackCases'
import { FeedbackCategoriesPage } from './FeedbackCategories'

type Tab = 'cases' | 'categories'

export function FeedbackPage() {
  const [tab, setTab] = useState<Tab>('cases')

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab('cases')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'cases' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Обращения
        </button>
        <button
          type="button"
          onClick={() => setTab('categories')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'categories' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Категории
        </button>
      </div>
      {tab === 'cases' ? <FeedbackCasesPage /> : <FeedbackCategoriesPage />}
    </div>
  )
}
