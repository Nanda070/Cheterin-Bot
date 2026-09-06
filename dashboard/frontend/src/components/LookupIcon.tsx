import { MagnifyingGlass } from '@phosphor-icons/react'

/** Lookup product mark — Phosphor fill, same language as Cheterin Sparkle BrandMark. */
export function LookupIcon({
  size = 20,
  className = 'text-primary',
}: {
  size?: number
  className?: string
}) {
  return <MagnifyingGlass size={size} weight="fill" className={className} aria-hidden />
}
