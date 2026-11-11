import { useEffect, useMemo, useState } from 'react'
import { getLocals } from '../api/inventory'
import { getReportingKpis, getReportingStatus, type ReportingKpis, type ReportingStatus, type WeeklyActivityRow } from '../api/reporting'

const dateFormat = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long' })
const dateTimeFormat = new Intl.DateTimeFormat('es-CO', { dateStyle: 'long', timeStyle: 'short' })

function parseDay(value: string): Date {
  return new Date(`${value}T12:00:00`)
}

function weekLabel(row: Pick<WeeklyActivityRow, 'week_start' | 'week_end'>): string {
  return `Semana del ${dateFormat.format(parseDay(row.week_start))} al ${dateFormat.format(parseDay(row.week_end))} de ${parseDay(row.week_end).getFullYear()}`
}

function ReportingDashboard() {
  const [kpis, setKpis] = useState<ReportingKpis | null>(null)
  const [status, setStatus] = useState<ReportingStatus | null>(null)
  const [localNames, setLocalNames] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([getReportingKpis(), getReportingStatus(), getLocals().catch(() => [])])
      .then(([kpiData, statusData, locals]) => {
        if (!active) return
        setKpis(kpiData)
        setStatus(statusData)
        setLocalNames(Object.fromEntries(locals.map((local) => [local.id, local.nombre])))
      })
      .catch((requestError: unknown) => {
        if (active) setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar el resumen ejecutivo.')
      })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const localLabel = (localId: string) => {
    if (localId === 'unknown') return 'Local sin identificar'
    return localNames[localId] ?? `Local ·${localId.slice(-4)}`
  }

  const weeks = useMemo(() => {
    const grouped = new Map<string, { label: string; rows: WeeklyActivityRow[]; total: number }>()
    for (const row of kpis?.rows ?? []) {
      const group = grouped.get(row.week_start) ?? { label: weekLabel(row), rows: [], total: 0 }
      group.rows.push(row)
      group.total += row.ticket_count
      grouped.set(row.week_start, group)
    }
    return [...grouped.entries()].sort(([a], [b]) => b.localeCompare(a)).map(([, group]) => group)
  }, [kpis])

  const peak = Math.max(1, ...weeks.flatMap((week) => week.rows.map((row) => row.ticket_count)))
  const salesPending = !kpis || kpis.rows.every((row) => row.sales_total_amount === null)

  if (loading) return <p className="empty-state">Cargando resumen ejecutivo...</p>
  if (error) return <div className="message message-error">{error}</div>

  return (
    <section className="reporting" aria-label="Resumen ejecutivo de Brasaland">
      {status?.stale && (
        <div className="message message-error" role="alert">
          <strong>Datos desactualizados.</strong>{' '}
          {status.last_successful_run_at
            ? `La última actualización correcta fue el ${dateTimeFormat.format(new Date(status.last_successful_run_at))}; se esperaba una cada semana.`
            : 'Todavía no hay ninguna actualización semanal completada.'}
        </div>
      )}
      <div className="kpi-grid">
        <article className="panel kpi-card">
          <span className="section-kicker">Dirección Ejecutiva</span>
          <h2>Ventas totales de la cadena (USD y COP)</h2>
          {salesPending ? (
            <>
              <strong className="kpi-pending">Pendiente</strong>
              <p>Pendiente de conectar con el sistema de caja (POS). Aún no se muestran cifras de ventas para no presentar datos inexactos.</p>
            </>
          ) : <p>Cifras disponibles.</p>}
          <p className="kpi-period">Período: se calculará cada semana (de lunes a domingo).</p>
        </article>
        <article className="panel kpi-card">
          <span className="section-kicker">Operación</span>
          <h2>Actividad semanal de movimientos de inventario</h2>
          <strong>{weeks[0]?.total ?? 0}</strong>
          <p>{weeks[0] ? `movimientos registrados en la ${weekLabel(weeks[0].rows[0]).toLowerCase()}` : 'Sin movimientos registrados todavía.'}</p>
          {status?.last_successful_run_at && <p className="kpi-period">Actualizado el {dateTimeFormat.format(new Date(status.last_successful_run_at))}</p>}
        </article>
      </div>
      <section className="panel list-panel">
        <div className="panel-heading list-heading">
          <div><span className="section-kicker">Detalle por semana y local</span><h2>Actividad semanal de movimientos de inventario</h2></div>
          <span className="record-count">{weeks.length} {weeks.length === 1 ? 'semana' : 'semanas'}</span>
        </div>
        {weeks.length === 0 ? <p className="empty-state">Todavía no hay datos semanales. Se generan cada lunes.</p> : weeks.map((week) => (
          <div className="week-block" key={week.label}>
            <h3>{week.label} <span>· {week.total} movimientos en total</span></h3>
            <div className="table-wrap"><table><thead><tr><th>Local</th><th>Movimientos de inventario</th><th aria-hidden="true" /></tr></thead>
              <tbody>{week.rows.map((row) => (
                <tr key={`${row.week_start}-${row.market}-${row.local_id}`}>
                  <td className="strong-cell">{localLabel(row.local_id)}</td>
                  <td>{row.ticket_count}</td>
                  <td className="bar-cell"><i style={{ width: `${Math.round((row.ticket_count / peak) * 100)}%` }} /></td>
                </tr>
              ))}</tbody></table></div>
          </div>
        ))}
      </section>
    </section>
  )
}

export default ReportingDashboard
