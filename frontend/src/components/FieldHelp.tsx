interface FieldHelpProps {
  term: string
  definition: string
}

/** Hover/focus definition tip for clinical terms unfamiliar to patients/caregivers. */
export function FieldHelp({ term, definition }: FieldHelpProps) {
  return (
    <button
      type="button"
      className="field-help__trigger"
      aria-label={`What does ${term} mean?`}
      title={definition}
    >
      ?
      <span className="field-help__tooltip" role="tooltip">
        {definition}
      </span>
    </button>
  )
}
