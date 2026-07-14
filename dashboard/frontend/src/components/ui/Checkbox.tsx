import { Check } from '@phosphor-icons/react'

interface CheckboxProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
  disabled?: boolean
}

export function Checkbox({ checked, onChange, label, disabled }: CheckboxProps) {
  return (
    <label className={`flex items-center gap-2 ${disabled ? 'opacity-50' : 'cursor-pointer'}`}>
      <button
        type="button"
        role="checkbox"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-[5px] border transition-colors duration-150 ${
          checked ? 'border-primary bg-primary' : 'border-border bg-background hover:border-muted'
        }`}
      >
        {checked && <Check size={12} weight="bold" className="text-white" />}
      </button>
      {label && <span className="text-sm text-foreground">{label}</span>}
    </label>
  )
}
