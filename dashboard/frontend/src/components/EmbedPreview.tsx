import type { EmbedSpec } from '../api/client'

interface Props {
  content: string
  embed: EmbedSpec
}

export function EmbedPreview({ content, embed }: Props) {
  const barColor = embed.color || '#4e5058'

  return (
    <div className="rounded-card border border-border bg-background p-4">
      {content && <p className="mb-2 whitespace-pre-wrap text-sm text-foreground">{content}</p>}
      <div className="flex rounded-control bg-surface" style={{ borderLeft: `4px solid ${barColor}` }}>
        <div className="flex-1 p-3">
          {embed.author.name && (
            <div className="mb-1 flex items-center gap-2 text-sm font-medium text-foreground">
              {embed.author.icon_url && <img src={embed.author.icon_url} alt="" className="h-5 w-5 rounded-full" />}
              <span>{embed.author.name}</span>
            </div>
          )}
          {embed.title && <p className="mb-1 text-base font-semibold text-foreground">{embed.title}</p>}
          {embed.description && (
            <p className="mb-2 whitespace-pre-wrap text-sm text-muted">{embed.description}</p>
          )}
          {embed.fields.length > 0 && (
            <div className="mb-2 grid grid-cols-2 gap-2">
              {embed.fields.map((field, index) => (
                <div key={index} className={field.inline ? '' : 'col-span-2'}>
                  <p className="text-xs font-semibold text-foreground">{field.name}</p>
                  <p className="whitespace-pre-wrap text-xs text-muted">{field.value}</p>
                </div>
              ))}
            </div>
          )}
          {embed.image.url && <img src={embed.image.url} alt="" className="mt-2 max-w-full rounded-control" />}
          {(embed.footer.text || embed.timestamp) && (
            <div className="mt-2 flex items-center gap-2 text-xs text-muted">
              {embed.footer.icon_url && (
                <img src={embed.footer.icon_url} alt="" className="h-4 w-4 rounded-full" />
              )}
              <span>
                {embed.footer.text}
                {embed.footer.text && embed.timestamp && ' • '}
                {embed.timestamp && new Date(embed.timestamp).toLocaleString()}
              </span>
            </div>
          )}
        </div>
        {embed.thumbnail.url && (
          <img src={embed.thumbnail.url} alt="" className="m-3 h-16 w-16 rounded-control object-cover" />
        )}
      </div>
    </div>
  )
}
