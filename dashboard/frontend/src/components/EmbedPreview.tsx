import type { EmbedSpec } from '../api/client'
import { normalizeEmbedSpec } from '../utils/embedUtils'

interface Props {
  content: string
  /** Single embed (welcome, feedback, events editors). */
  embed?: EmbedSpec
  /** All embeds of a multi-embed message; wins over `embed`. */
  embeds?: EmbedSpec[]
}

function hasVisibleContent(spec: EmbedSpec): boolean {
  return Boolean(
    spec.title ||
      spec.description ||
      spec.author.name ||
      spec.footer.text ||
      spec.timestamp ||
      spec.fields.length > 0 ||
      spec.image.url ||
      spec.thumbnail.url,
  )
}

function EmbedCard({ spec }: { spec: EmbedSpec }) {
  const barColor = spec.color || '#4e5058'

  return (
    <div className="flex rounded-control bg-surface" style={{ borderLeft: `4px solid ${barColor}` }}>
      <div className="min-w-0 flex-1 p-3">
        {spec.author.name && (
          <div className="mb-1 flex items-center gap-2 text-sm font-medium text-foreground">
            {spec.author.icon_url && <img src={spec.author.icon_url} alt="" className="h-5 w-5 rounded-full" />}
            <span>{spec.author.name}</span>
          </div>
        )}
        {spec.title && <p className="mb-1 text-base font-semibold text-foreground">{spec.title}</p>}
        {spec.description && <p className="mb-2 whitespace-pre-wrap text-sm text-muted">{spec.description}</p>}
        {spec.fields.length > 0 && (
          <div className="mb-2 grid grid-cols-2 gap-2">
            {spec.fields.map((field, index) => (
              <div key={index} className={field.inline ? '' : 'col-span-2'}>
                <p className="text-xs font-semibold text-foreground">{field.name}</p>
                <p className="whitespace-pre-wrap text-xs text-muted">{field.value}</p>
              </div>
            ))}
          </div>
        )}
        {spec.image.url && <img src={spec.image.url} alt="" className="mt-2 max-w-full rounded-control" />}
        {(spec.footer.text || spec.timestamp) && (
          <div className="mt-2 flex items-center gap-2 text-xs text-muted">
            {spec.footer.icon_url && <img src={spec.footer.icon_url} alt="" className="h-4 w-4 rounded-full" />}
            <span>
              {spec.footer.text}
              {spec.footer.text && spec.timestamp && ' • '}
              {spec.timestamp && new Date(spec.timestamp).toLocaleString()}
            </span>
          </div>
        )}
      </div>
      {spec.thumbnail.url && <img src={spec.thumbnail.url} alt="" className="m-3 h-16 w-16 rounded-control object-cover" />}
    </div>
  )
}

export function EmbedPreview({ content, embed, embeds }: Props) {
  const all = (embeds ?? [embed]).map((spec) => normalizeEmbedSpec(spec))
  // Blank slots of a multi-embed message are not sent, so they are not previewed either;
  // one card always stays so the preview never collapses to nothing.
  const filled = all.filter(hasVisibleContent)
  const specs = filled.length > 0 ? filled : all.slice(0, 1)

  return (
    <div className="rounded-card border border-border bg-background p-4">
      {content && <p className="mb-2 whitespace-pre-wrap break-words text-sm text-foreground">{content}</p>}
      <div className="flex flex-col gap-2">
        {specs.map((spec, index) => (
          <EmbedCard key={index} spec={spec} />
        ))}
      </div>
    </div>
  )
}
