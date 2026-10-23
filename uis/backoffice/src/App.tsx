import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { createIncident, getIncidents } from './api/incidents'
import SelectField from './components/SelectField'
import { useFormTelemetry } from './hooks/useFormTelemetry'
import { track } from './services/telemetry'
import { trackedLazyImport, trackOperationFailed } from './services/telemetryErrors'
import { areas, channels, incidentTypes, severities, statuses, type Area, type Incident, type IncidentFilters, type IncidentType, type NewIncident, type Severity } from '@repo/shared-types'

const InventoryManager = lazy(trackedLazyImport('inventory', () => import('./InventoryManager')))
const IncidentDetailView = lazy(trackedLazyImport('incident_detail', () => import('./components/IncidentDetailView')))

type View = 'incidents' | 'inventory'
type DetailTrigger = 'table_click' | 'table_enter' | 'after_create'

function activeFilters(filters: IncidentFilters): IncidentFilters {
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => value)) as IncidentFilters
}

const emptyForm: NewIncident = { canal: channels[0], tipo: incidentTypes[0], severidad: severities[1], area_responsable: areas[0], autor: '' }

function App() {
  const [activeView, setActiveView] = useState<View>('incidents')
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [operationalIncidents, setOperationalIncidents] = useState<Incident[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filters, setFilters] = useState<IncidentFilters>({})
  const [form, setForm] = useState<NewIncident>(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const initialViewTracked = useRef(false)
  const { bindForm: bindIncidentForm, ...incidentForm } = useFormTelemetry('incident_create')

  const loadIncidents = async (nextFilters = filters) => {
    setLoading(true)
    setError('')
    try {
      const data = await getIncidents(nextFilters)
      setIncidents(data)
      if (selectedId && !data.some((incident) => incident.id === selectedId)) setSelectedId(null)
      return data
    } catch (requestError) {
      trackOperationFailed('incident_list_load', requestError)
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
    if (!initialViewTracked.current) {
      initialViewTracked.current = true
      track('navigation.section_viewed', { view: 'incidents', trigger: 'initial' })
    }
    void Promise.all([getIncidents({}), getIncidents({})]).then(([tableData, operationalData]) => {
      setIncidents(tableData)
      setOperationalIncidents(operationalData)
    }).catch((requestError: unknown) => {
      trackOperationFailed('initial_load', requestError)
      setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar la informacion.')
    }).finally(() => setLoading(false))
  }, [])

  const changeView = (view: View) => {
    if (view === activeView) return
    setActiveView(view)
    track('navigation.section_viewed', { view, trigger: 'tab_change' })
  }

  const openDetail = (id: string, trigger: DetailTrigger) => {
    setSelectedId(id)
    track('incident.detail_opened', { incidentId: id, trigger })
  }

  const handleFilterChange = (key: keyof IncidentFilters, value: string) => {
    const nextFilters = activeFilters({ ...filters, [key]: value || undefined })
    setFilters(nextFilters)
    track('incident.filters_applied', { filters: nextFilters, changedFilter: key })
    void loadIncidents(nextFilters).then((data) => {
      if (data?.length === 0 && Object.keys(nextFilters).length > 0) {
        track('incident.filter_empty_result', { filters: nextFilters, rowCount: 0 }, data)
      }
    })
  }

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true); setError(''); setNotice('')
    const formAttemptId = incidentForm.start()
    try {
      const incident = await createIncident(form)
      incidentForm.complete()
      setForm(emptyForm); openDetail(incident.id, 'after_create'); setNotice('Incidencia registrada correctamente.')
      await Promise.all([loadIncidents(), loadOperationalIncidents()])
    } catch (requestError) {
      trackOperationFailed('incident_create', requestError, formAttemptId)
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
          onClick={() => changeView('incidents')}
        >
          Incidencias
        </button>
        <button
          className={`domain-tab ${activeView === 'inventory' ? 'is-active' : ''}`}
          type="button"
          role="tab"
          aria-selected={activeView === 'inventory'}
          onClick={() => changeView('inventory')}
        >
          Inventario
        </button>
      </nav>
      {activeView === 'inventory' ? (
        <Suspense fallback={<p className="empty-state">Cargando inventario...</p>}>
          <InventoryManager />
        </Suspense>
      ) : <>
      {(error || notice) && <div className={`message ${error ? 'message-error' : 'message-success'}`}>{error || notice}</div>}
      <section className="summary-grid" aria-label="Resumen operativo">
        <div className="summary-lead"><span className="section-kicker">Vista operativa</span><strong>{openIncidents.length}</strong><span>incidencias abiertas en esta consulta</span></div>
        {severities.map((severity) => <div className={`severity-card severity-${severity.toLowerCase()}`} key={severity}><span>{severity}</span><strong>{openIncidents.filter((incident) => incident.severidad === severity).length}</strong></div>)}
      </section>
      <div className="workspace">
        <section className="panel form-panel">
          <div className="panel-heading"><div><span className="section-kicker">Nueva entrada</span><h2>Registrar incidencia</h2></div><span className="step-mark">01</span></div>
          <form ref={bindIncidentForm} onChange={() => { incidentForm.start() }} onSubmit={handleCreate}>
            <SelectField label="Canal" name="canal" value={form.canal} options={channels} onChange={(value) => setForm({ ...form, canal: value as NewIncident['canal'] })} />
            <SelectField label="Tipo de incidencia" name="tipo" value={form.tipo} options={incidentTypes} onChange={(value) => setForm({ ...form, tipo: value as IncidentType })} />
            <div className="field-row"><SelectField label="Severidad" name="severidad" value={form.severidad} options={severities} onChange={(value) => setForm({ ...form, severidad: value as Severity })} /><SelectField label="Área responsable" name="area_responsable" value={form.area_responsable} options={areas} onChange={(value) => setForm({ ...form, area_responsable: value as Area })} /></div>
            <label className="field"><span>Autor del reporte</span><input name="autor" required value={form.autor} onChange={(event) => setForm({ ...form, autor: event.target.value })} placeholder="Nombre o sistema" /></label>
            <button className="primary-button" type="submit" disabled={saving}>{saving ? 'Guardando...' : 'Registrar incidencia'} <span>→</span></button>
          </form>
        </section>
        <section className="panel list-panel">
          <div className="panel-heading list-heading"><div><span className="section-kicker">Seguimiento</span><h2>Incidencias registradas</h2></div><span className="record-count">{incidents.length} registros</span></div>
          <div className="filters"><FilterSelect label="Estado" value={filters.estado || ''} options={statuses} onChange={(value) => handleFilterChange('estado', value)} /><FilterSelect label="Severidad" value={filters.severidad || ''} options={severities} onChange={(value) => handleFilterChange('severidad', value)} /><FilterSelect label="Área" value={filters.area_responsable || ''} options={areas} onChange={(value) => handleFilterChange('area_responsable', value)} /></div>
          {loading ? <p className="empty-state">Cargando incidencias...</p> : incidents.length === 0 ? <p className="empty-state">No hay incidencias para estos filtros.</p> : <IncidentTable incidents={incidents} selectedId={selectedId} onSelect={openDetail} />}
        </section>
      </div>
      {selectedId && <Suspense fallback={<div className="detail-backdrop" role="presentation"><aside className="detail-drawer"><p className="empty-state">Cargando detalle...</p></aside></div>}><IncidentDetailView id={selectedId} onUpdated={() => Promise.all([loadIncidents(), loadOperationalIncidents()]).then(() => undefined)} onClose={() => setSelectedId(null)} setError={setError} /></Suspense>}
      </>}
    </main>
  )
}

function FilterSelect<T extends string>({ label, value, options, onChange }: { label: string; value: string; options: readonly T[]; onChange: (value: string) => void }) {
  return <label className="filter-field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">Todos</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>
}

function IncidentTable({ incidents, selectedId, onSelect }: { incidents: Incident[]; selectedId: string | null; onSelect: (id: string, trigger: DetailTrigger) => void }) {
  return <div className="table-wrap"><table><thead><tr><th>Canal</th><th>Tipo</th><th>Severidad</th><th>Área responsable</th><th>Estado</th><th>Autor</th></tr></thead><tbody>{incidents.map((incident) => <tr className={selectedId === incident.id ? 'selected-row' : ''} key={incident.id} onClick={() => onSelect(incident.id, 'table_click')} tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && onSelect(incident.id, 'table_enter')}><td>{incident.canal}</td><td className="strong-cell">{incident.tipo}</td><td><span className={`badge badge-${incident.severidad.toLowerCase()}`}>{incident.severidad}</span></td><td>{incident.area_responsable}</td><td><span className="status-dot"><i />{incident.estado}</span></td><td>{incident.autor}</td></tr>)}</tbody></table></div>
}

export default App
