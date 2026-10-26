export default function SelectField<T extends string>({
  label,
  value,
  options,
  onChange,
  placeholder,
  required,
  disabled,
  name,
}: {
  label: string
  value: T | ''
  options: readonly (T | { value: T; label: string })[]
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
  disabled?: boolean
  name?: string
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select name={name} value={value} onChange={(event) => onChange(event.target.value)} required={required} disabled={disabled}>
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((option) => {
          const optionValue = typeof option === 'string' ? option : option.value
          const optionLabel = typeof option === 'string' ? option : option.label
          return <option key={optionValue} value={optionValue}>{optionLabel}</option>
        })}
      </select>
    </label>
  )
}
