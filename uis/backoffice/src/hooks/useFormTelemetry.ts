import { useCallback, useEffect, useRef } from 'react'
import { newFormAttemptId, track } from '../services/telemetry'

export type TrackedFormType = 'incident_create' | 'article_create' | 'local_create' | 'movement_create'

const KNOWN_FIELDS = new Set([
  'articulo_id', 'local', 'tipo', 'cantidad', 'autor', 'fecha', 'motivo', 'nombre', 'categoria',
  'unidad_medida', 'punto_reorden', 'estado', 'severidad', 'area_responsable', 'canal',
])
const MAX_ELAPSED_MS = 86_400_000

function validationRule(validity: ValidityState): string {
  if (validity.valueMissing) return 'required'
  if (validity.typeMismatch || validity.badInput) return 'invalid_type'
  if (validity.rangeUnderflow) return 'nonnegative_required'
  return 'other'
}

/**
 * Tracks one form's attempt lifecycle via track(): form.started on first edit,
 * form.validation_blocked on native constraint failures and an inferred form.abandoned on exit.
 */
export function useFormTelemetry(formType: TrackedFormType, { abandonOnUnmount = false } = {}) {
  const attempt = useRef<{ id: string; startedAt: number } | null>(null)

  const start = useCallback((): string => {
    if (!attempt.current) {
      attempt.current = { id: newFormAttemptId(), startedAt: Date.now() }
      track('form.started', { formType, formAttemptId: attempt.current.id })
    }
    return attempt.current.id
  }, [formType])

  const complete = useCallback(() => {
    attempt.current = null
  }, [])

  const attemptId = useCallback(() => attempt.current?.id, [])

  const abandon = useCallback((reason: 'tab_change' | 'page_exit') => {
    if (!attempt.current) return
    track('form.abandoned', {
      formType,
      formAttemptId: attempt.current.id,
      reason,
      elapsedMs: Math.min(Date.now() - attempt.current.startedAt, MAX_ELAPSED_MS),
      inferred: true,
    })
    attempt.current = null
  }, [formType])

  // Native "invalid" does not bubble, so it is observed in the capture phase on the form.
  const bindForm = useCallback((form: HTMLFormElement | null) => {
    if (!form) return
    const onInvalid = (event: Event) => {
      const control = event.target as HTMLInputElement | HTMLSelectElement
      track('form.validation_blocked', {
        formType,
        formAttemptId: start(),
        field: KNOWN_FIELDS.has(control.name) ? control.name : 'unknown',
        rule: validationRule(control.validity),
      })
    }
    form.addEventListener('invalid', onInvalid, true)
    return () => form.removeEventListener('invalid', onInvalid, true)
  }, [formType, start])

  useEffect(() => {
    const onPageHide = () => abandon('page_exit')
    window.addEventListener('pagehide', onPageHide)
    return () => {
      window.removeEventListener('pagehide', onPageHide)
      if (abandonOnUnmount) abandon('tab_change')
    }
  }, [abandon, abandonOnUnmount])

  return { bindForm, start, complete, attemptId }
}
