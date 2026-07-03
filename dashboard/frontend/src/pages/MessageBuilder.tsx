import { useState } from 'react'
import { ReactionRolesPage } from './ReactionRoles'
import { EmbedBuilderPage } from './EmbedBuilder'

type Tab = 'reaction-roles' | 'embeds'

export function MessageBuilderPage() {
  const [tab, setTab] = useState<Tab>('reaction-roles')

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab('reaction-roles')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'reaction-roles' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Roles
        </button>
        <button
          type="button"
          onClick={() => setTab('embeds')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'embeds' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Эмбеды
        </button>
      </div>
      {tab === 'reaction-roles' ? <ReactionRolesPage /> : <EmbedBuilderPage />}
    </div>
  )
}
