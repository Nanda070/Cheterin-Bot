type Props = {
  name: string
  avatarUrl?: string | null
  size?: 'sm' | 'md' | 'lg'
  alive?: boolean
  className?: string
}

const SIZE = {
  sm: 'h-8 w-8 text-[10px]',
  md: 'h-11 w-11 text-xs',
  lg: 'h-14 w-14 text-sm',
} as const

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] ?? ''}${parts[1][0] ?? ''}`.toUpperCase()
}

export function GameAvatar({ name, avatarUrl, size = 'md', alive = true, className = '' }: Props) {
  return (
    <div
      className={`relative shrink-0 overflow-hidden rounded-full ring-2 ring-border/80 ${SIZE[size]} ${
        alive ? '' : 'opacity-45 grayscale'
      } ${className}`}
    >
      {avatarUrl ? (
        <img src={avatarUrl} alt="" className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-primary-muted font-semibold text-foreground">
          {initials(name)}
        </div>
      )}
    </div>
  )
}
