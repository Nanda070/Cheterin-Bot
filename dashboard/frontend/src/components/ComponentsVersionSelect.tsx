import { useT } from '../context/LanguageContext'
import { Select } from './ui/Select'

export type ComponentsVersion = 'v1' | 'v2'

type Props = {
  value: ComponentsVersion
  onChange: (version: ComponentsVersion) => void
  className?: string
}

/** Discord Message Components V1/V2 selector (above templates / publish controls). */
export function ComponentsVersionSelect({ value, onChange, className }: Props) {
  const t = useT()
  return (
    <div className={`flex flex-col gap-1 ${className || ''}`}>
      <label className="text-sm font-medium text-foreground" htmlFor="components-version">
        {t('componentsVersion.label')}
      </label>
      <Select
        id="components-version"
        value={value}
        onChange={(id) => onChange(id === 'v2' ? 'v2' : 'v1')}
        options={[
          { id: 'v1', name: t('componentsVersion.v1') },
          { id: 'v2', name: t('componentsVersion.v2') },
        ]}
      />
      <p className="text-xs text-muted">{t(value === 'v2' ? 'componentsVersion.hintV2' : 'componentsVersion.hintV1')}</p>
    </div>
  )
}
