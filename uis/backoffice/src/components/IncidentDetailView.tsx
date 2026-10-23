import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { getIncident, updateIncident } from '../api/incidents'
import { areas, statuses, type Area, type Status } from '@repo/shared-types'
import SelectField from './SelectField'
import { formatDate } from '../utils/formatDate'

type IncidentDetailViewProps = {
  id: string
  onUpdated: () => void
  onClose: () => void
  setError: (message: string) => void
}

function IncidentDetailView({ id, onUpdated, onClose, setError }: IncidentDetailViewProps) {
  const [detail, setDetail] = useState<Awaited<ReturnType<typeof getIncident>> | null>(null)
  const [status, setStatus] = useState<Status | ''>('')
  const [area, setArea] = useState<Area | ''>('')
  const [author, setAuthor] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    void getIncident(id).then((data) => { setDetail(data); setStatus(data.incidencia.estado); setArea(data.incidencia.area_responsable) }).catch((error: unknown) => setError(error instanceof Error ? error.message : 'No se pudo cargar el detalle.'))
  }, [id, setError])

  const saveChanges = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!detail || !author.trim()) return
    setSaving(true)
    try {
      await updateIncident(id, { estado: status || undefined, area_responsable: area || undefined, autor: author.trim() })
      setAuthor(''); onUpdated()
      const fresh = await getIncident(id); setDetail(fresh); setStatus(fresh.incidencia.estado); setArea(fresh.incidencia.area_responsable)
    } catch (error) { setError(error instanceof Error ? error.message : 'No se pudo actualizar la incidencia.') } finally { setSaving(false) }
  }

  return <div className="detail-backdrop" role="presentation" onClick={onClose}><aside className="detail-drawer" onClick={(event) => event.stopPropagation()}>{!detail ? <p className="empty-state">Cargando detalle...</p> : <><div className="drawer-header"><div><span className="section-kicker">Ficha de incidencia</span><h2>{detail.incidencia.tipo}</h2></div><button className="close-button" type="button" onClick={onClose} aria-label="Cerrar detalle">×</button></div><div className="detail-meta"><span className={`badge badge-${detail.incidencia.severidad.toLowerCase()}`}>{detail.incidencia.severidad}</span><span>{detail.incidencia.canal}</span><span>{detail.incidencia.autor}</span></div><dl className="detail-grid"><div><dt>ID</dt><dd>{detail.incidencia.id}</dd></div><div><dt>Creada</dt><dd>{formatDate(detail.incidencia.created_at)}</dd></div><div><dt>Área</dt><dd>{detail.incidencia.area_responsable}</dd></div><div><dt>Actualizada</dt><dd>{formatDate(detail.incidencia.updated_at)}</dd></div></dl><form className="update-form" onSubmit={saveChanges}><span className="section-kicker">Actualizar seguimiento</span><div className="field-row"><SelectField label="Estado" value={status} options={statuses} onChange={(value) => setStatus(value as Status)} /><SelectField label="Área responsable" value={area} options={areas} onChange={(value) => setArea(value as Area)} /></div><label className="field"><span>Autor del cambio</span><input required value={author} onChange={(event) => setAuthor(event.target.value)} placeholder="Quién realiza el cambio" /></label><button className="primary-button" type="submit" disabled={saving}>{saving ? 'Actualizando...' : 'Guardar cambios'} <span>→</span></button></form><div className="history"><div className="history-title"><span className="section-kicker">Trazabilidad</span><strong>{detail.historial.length} cambios</strong></div>{detail.historial.length === 0 ? <p className="empty-state">Sin cambios registrados.</p> : detail.historial.map((change) => <div className="history-item" key={change.id}><span className="history-field">{change.campo}</span><p><strong>{change.valor_anterior}</strong> <span>→</span> {change.valor_nuevo}</p><small>{change.autor} · {formatDate(change.timestamp)}</small></div>)}</div></>}</aside></div>
}

export default IncidentDetailView
