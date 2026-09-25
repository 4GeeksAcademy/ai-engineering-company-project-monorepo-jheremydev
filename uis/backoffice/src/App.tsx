import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { createIncident, getIncident, getIncidents, updateIncident } from './api/incidents'
import InventoryManager from './InventoryManager'
import { areas, channels, incidentTypes, severities, statuses, type Area, type Incident, type IncidentFilters, type IncidentType, type NewIncident, type Severity, type Status } from '@repo/shared-types'
import './App.css'

const emptyForm: NewIncident = { canal: channels[0], tipo: incidentTypes[0], severidad: severities[1], area_responsable: areas[0], autor: '' }

function App() {
  const [activeView, setActiveView] = useState<'incidents' | 'inventory'>('incidents')
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [operationalIncidents, setOperationalIncidents] = useState<Incident[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filters, setFilters] = useState<IncidentFilters>({})
  const [form, setForm] = useState<NewIncident>(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadIncidents = async (nextFilters = filters) => {
    setLoading(true)
    setError('')
    try {
      const data = await getIncidents(nextFilters)
      setIncidents(data)
      if (selectedId && !data.some((incident) => incident.id === selectedId)) setSelectedId(null)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar la informacion.')
    } finally {
      setLoading(false)
    }
  }

  const loadOperationalIncidents = async () => {
    try {
      const data = await getIncidents({})
      setOperationalIncidents(data)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar el resumen operativo.')
    }
  }

  useEffect(() => {
    void Promise.all([getIncidents({}), getIncidents({})]).then(([tableData, operationalData]) => {
      setIncidents(tableData)
      setOperationalIncidents(operationalData)
    }).catch((requestError: unknown) => {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar la informacion.')
    }).finally(() => setLoading(false))
  }, [])

  const handleFilterChange = (key: keyof IncidentFilters, value: string) => {
    const nextFilters = { ...filters, [key]: value || undefined }
    setFilters(nextFilters)
    void loadIncidents(nextFilters)
  }

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true); setError(''); setNotice('')
    try {
      const incident = await createIncident(form)
      setForm(emptyForm); setSelectedId(incident.id); setNotice('Incidencia registrada correctamente.')
      await Promise.all([loadIncidents(), loadOperationalIncidents()])
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo registrar la incidencia.')
    } finally { setSaving(false) }
  }

  const openIncidents = operationalIncidents.filter((incident) => incident.estado !== 'Cerrada' && incident.estado !== 'Resuelta')

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">Brasaland Digital / Operaciones</p><h1>{activeView === 'inventory' ? 'Gestor de inventario' : 'Centro de incidencias'}</h1></div>
        <div className="live-status"><span /> API conectada por configuración</div>
      </header>
      <nav className="domain-tabs" role="tablist" aria-label="Módulos operativos">
        <button
          className={`domain-tab ${activeView === 'incidents' ? 'is-active' : ''}`}
          type="button"
          role="tab"
          aria-selected={activeView === 'incidents'}
          onClick={() => setActiveView('incidents')}
        >
          Incidencias
        </button>
        <button
          className={`domain-tab ${activeView === 'inventory' ? 'is-active' : ''}`}
          type="button"
          role="tab"
          aria-selected={activeView === 'inventory'}
          onClick={() => setActiveView('inventory')}
        >
          Inventario
        </button>
      </nav>
      {activeView === 'inventory' ? <InventoryManager /> : <>
      {(error || notice) && <div className={`message ${error ? 'message-error' : 'message-success'}`}>{error || notice}</div>}
      <section className="summary-grid" aria-label="Resumen operativo">
        <div className="summary-lead"><span className="section-kicker">Vista operativa</span><strong>{openIncidents.length}</strong><span>incidencias abiertas en esta consulta</span></div>
        {severities.map((severity) => <div className={`severity-card severity-${severity.toLowerCase()}`} key={severity}><span>{severity}</span><strong>{openIncidents.filter((incident) => incident.severidad === severity).length}</strong></div>)}
      </section>
      <div className="workspace">
        <section className="panel form-panel">
          <div className="panel-heading"><div><span className="section-kicker">Nueva entrada</span><h2>Registrar incidencia</h2></div><span className="step-mark">01</span></div>
          <form onSubmit={handleCreate}>
            <SelectField label="Canal" value={form.canal} options={channels} onChange={(value) => setForm({ ...form, canal: value as NewIncident['canal'] })} />
            <SelectField label="Tipo de incidencia" value={form.tipo} options={incidentTypes} onChange={(value) => setForm({ ...form, tipo: value as IncidentType })} />
            <div className="field-row"><SelectField label="Severidad" value={form.severidad} options={severities} onChange={(value) => setForm({ ...form, severidad: value as Severity })} /><SelectField label="Área responsable" value={form.area_responsable} options={areas} onChange={(value) => setForm({ ...form, area_responsable: value as Area })} /></div>
            <label className="field"><span>Autor del reporte</span><input required value={form.autor} onChange={(event) => setForm({ ...form, autor: event.target.value })} placeholder="Nombre o sistema" /></label>
            <button className="primary-button" type="submit" disabled={saving}>{saving ? 'Guardando...' : 'Registrar incidencia'} <span>→</span></button>
          </form>
        </section>
        <section className="panel list-panel">
          <div className="panel-heading list-heading"><div><span className="section-kicker">Seguimiento</span><h2>Incidencias registradas</h2></div><span className="record-count">{incidents.length} registros</span></div>
          <div className="filters"><FilterSelect label="Estado" value={filters.estado || ''} options={statuses} onChange={(value) => handleFilterChange('estado', value)} /><FilterSelect label="Severidad" value={filters.severidad || ''} options={severities} onChange={(value) => handleFilterChange('severidad', value)} /><FilterSelect label="Área" value={filters.area_responsable || ''} options={areas} onChange={(value) => handleFilterChange('area_responsable', value)} /></div>
          {loading ? <p className="empty-state">Cargando incidencias...</p> : incidents.length === 0 ? <p className="empty-state">No hay incidencias para estos filtros.</p> : <IncidentTable incidents={incidents} selectedId={selectedId} onSelect={setSelectedId} />}
        </section>
      </div>
      {selectedId && <IncidentDetailView id={selectedId} onUpdated={() => Promise.all([loadIncidents(), loadOperationalIncidents()]).then(() => undefined)} onClose={() => setSelectedId(null)} setError={setError} />}
      </>}
    </main>
  )
}

function SelectField<T extends string>({ label, value, options, onChange }: { label: string; value: T | ''; options: readonly T[]; onChange: (value: string) => void }) {
  return <label className="field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>
}

function FilterSelect<T extends string>({ label, value, options, onChange }: { label: string; value: string; options: readonly T[]; onChange: (value: string) => void }) {
  return <label className="filter-field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">Todos</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>
}

function IncidentTable({ incidents, selectedId, onSelect }: { incidents: Incident[]; selectedId: string | null; onSelect: (id: string) => void }) {
  return <div className="table-wrap"><table><thead><tr><th>Canal</th><th>Tipo</th><th>Severidad</th><th>Área responsable</th><th>Estado</th><th>Autor</th></tr></thead><tbody>{incidents.map((incident) => <tr className={selectedId === incident.id ? 'selected-row' : ''} key={incident.id} onClick={() => onSelect(incident.id)} tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && onSelect(incident.id)}><td>{incident.canal}</td><td className="strong-cell">{incident.tipo}</td><td><span className={`badge badge-${incident.severidad.toLowerCase()}`}>{incident.severidad}</span></td><td>{incident.area_responsable}</td><td><span className="status-dot"><i />{incident.estado}</span></td><td>{incident.autor}</td></tr>)}</tbody></table></div>
}

function IncidentDetailView({ id, onUpdated, onClose, setError }: { id: string; onUpdated: () => void; onClose: () => void; setError: (message: string) => void }) {
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export default App
