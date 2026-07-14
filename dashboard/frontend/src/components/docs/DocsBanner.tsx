import bannerImg from '../../assets/docs-banner.webp'

export function DocsBanner() {
  return (
    <div className="relative mb-6 h-44 w-full overflow-hidden rounded-card border border-border sm:h-52">
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-cover bg-center opacity-70"
        style={{ backgroundImage: `url(${bannerImg})` }}
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-gradient-to-t from-background via-background/75 to-background/15"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-gradient-to-r from-background/85 via-transparent to-primary-muted"
      />
      <div className="relative flex h-full flex-col justify-end gap-1 p-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-primary">Документация</p>
        <p className="text-2xl font-semibold text-foreground sm:text-3xl">Cheterin</p>
      </div>
    </div>
  )
}
