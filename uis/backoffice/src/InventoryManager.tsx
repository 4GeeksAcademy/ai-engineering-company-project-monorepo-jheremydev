import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  inventoryCategories,
  inventoryLocals,
  inventoryUnits,
  movementTypes,
  type InventoryArticle,
  type InventoryCategory,
  type InventoryLocal,
  type InventoryMovement,
  type InventoryStock,
  type MovementType,
  type NewInventoryArticle,
  type NewInventoryMovement,
  type InventoryUnit,
} from '@repo/shared-types'
import {
  createArticle,
  createMovement,
  getArticles,
  getMovements,
  getStock,
} from './api/inventory'

type MovementFormState = Omit<NewInventoryMovement, 'articulo_id'>

const createEmptyArticleForm = (): NewInventoryArticle => ({
  nombre: '',
  categoria: inventoryCategories[0],
  unidad_medida: inventoryUnits[0],
})

function localDateTimeValue() {
  const now = new Date()
  const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
  return localDate.toISOString().slice(0, 16)
}

const createEmptyMovementForm = (): MovementFormState => ({
  local: inventoryLocals[0],
  tipo: movementTypes[0],
  cantidad: '',
  autor: '',
  fecha: localDateTimeValue(),
  motivo: '',
})

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function InventoryManager() {
  const [articles, setArticles] = useState<InventoryArticle[]>([])
  const [movements, setMovements] = useState<InventoryMovement[]>([])
  const [selectedArticleId, setSelectedArticleId] = useState('')
  const [stockArticleId, setStockArticleId] = useState('')
  const [stockLocal, setStockLocal] = useState<InventoryLocal>(inventoryLocals[0])
  const [stock, setStock] = useState<InventoryStock | null>(null)
  const [articleForm, setArticleForm] = useState<NewInventoryArticle>(createEmptyArticleForm)
  const [movementForm, setMovementForm] = useState<MovementFormState>(createEmptyMovementForm)
  const [loading, setLoading] = useState(true)
  const [savingArticle, setSavingArticle] = useState(false)
  const [savingMovement, setSavingMovement] = useState(false)
  const [loadingStock, setLoadingStock] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let active = true
    void Promise.all([getArticles(), getMovements()])
      .then(([articleData, movementData]) => {
        if (!active) return
        setArticles(articleData)
        setMovements(movementData)
        setSelectedArticleId(articleData[0]?.id ?? '')
        setStockArticleId(articleData[0]?.id ?? '')
      })
      .catch((requestError: unknown) => {
        if (active) setError(errorMessage(requestError, 'No se pudo cargar el inventario.'))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const reloadInventory = async () => {
    const [articleData, movementData] = await Promise.all([getArticles(), getMovements()])
    setArticles(articleData)
    setMovements(movementData)
  }

  const handleCreateArticle = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSavingArticle(true)
    setError('')
    setNotice('')
    try {
      const article = await createArticle({
        ...articleForm,
        nombre: articleForm.nombre.trim(),
      })
      setArticleForm(createEmptyArticleForm())
      setSelectedArticleId(article.id)
      setStockArticleId(article.id)
      setStock(null)
      await reloadInventory()
      setNotice('Artículo registrado correctamente.')
    } catch (requestError) {
      setError(errorMessage(requestError, 'No se pudo registrar el artículo.'))
    } finally {
      setSavingArticle(false)
    }
  }

  const handleCreateMovement = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSavingMovement(true)
    setError('')
    setNotice('')
    try {
      const payload: NewInventoryMovement = {
        articulo_id: selectedArticleId,
        local: movementForm.local,
        tipo: movementForm.tipo,
        cantidad: movementForm.cantidad,
        autor: movementForm.autor.trim(),
        fecha: movementForm.fecha,
        ...(movementForm.motivo?.trim() ? { motivo: movementForm.motivo.trim() } : {}),
      }
      await createMovement(payload)
      setMovementForm((current) => ({ ...current, cantidad: '', motivo: '' }))
      await reloadInventory()
      if (stock && stock.articulo_id === payload.articulo_id && stock.local === payload.local) {
        setStock(await getStock(payload.articulo_id, payload.local))
      }
      setNotice('Movimiento registrado correctamente.')
    } catch (requestError) {
      setError(errorMessage(requestError, 'No se pudo registrar el movimiento.'))
    } finally {
      setSavingMovement(false)
    }
  }

  const handleStockLookup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoadingStock(true)
    setError('')
    setNotice('')
    setStock(null)
    try {
      const result = await getStock(stockArticleId, stockLocal)
      setStock(result)
    } catch (requestError) {
      setError(errorMessage(requestError, 'No se pudo consultar el stock.'))
    } finally {
      setLoadingStock(false)
    }
  }

  const selectArticle = (articleId: string) => {
    setSelectedArticleId(articleId)
    setStockArticleId(articleId)
    setStock(null)
  }

  return (
    <div className="inventory-page">
      {(error || notice) && (
        <div
          className={`message ${error ? 'message-error' : 'message-success'}`}
          role={error ? 'alert' : 'status'}
        >
          {error || notice}
        </div>
      )}

      <div className="inventory-workspace">
        <div className="inventory-column">
          <section className="panel form-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">Catálogo común</span>
                <h2>Registrar artículo</h2>
              </div>
              <span className="step-mark">01</span>
            </div>
            <form onSubmit={handleCreateArticle}>
              <label className="field">
                <span>Nombre</span>
                <input
                  required
                  value={articleForm.nombre}
                  onChange={(event) => setArticleForm({ ...articleForm, nombre: event.target.value })}
                />
              </label>
              <label className="field">
                <span>Categoría</span>
                <select
                  value={articleForm.categoria}
                  onChange={(event) => setArticleForm({
                    ...articleForm,
                    categoria: event.target.value as InventoryCategory,
                  })}
                >
                  {inventoryCategories.map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Unidad de medida</span>
                <select
                  value={articleForm.unidad_medida}
                  onChange={(event) => setArticleForm({
                    ...articleForm,
                    unidad_medida: event.target.value as InventoryUnit,
                  })}
                >
                  {inventoryUnits.map((unit) => (
                    <option key={unit} value={unit}>{unit}</option>
                  ))}
                </select>
              </label>
              <button className="primary-button" type="submit" disabled={savingArticle}>
                {savingArticle ? 'Guardando...' : 'Registrar artículo'} <span>→</span>
              </button>
            </form>
          </section>

          <section className="panel list-panel">
            <div className="panel-heading list-heading">
              <div>
                <span className="section-kicker">Selección</span>
                <h2>Artículos registrados</h2>
              </div>
              <span className="record-count">{articles.length} artículos</span>
            </div>
            {loading ? (
              <p className="empty-state">Cargando artículos...</p>
            ) : articles.length === 0 ? (
              <p className="empty-state">No hay artículos registrados.</p>
            ) : (
              <div className="inventory-article-list">
                {articles.map((article) => (
                  <button
                    className={`inventory-article-option ${selectedArticleId === article.id ? 'is-selected' : ''}`}
                    type="button"
                    key={article.id}
                    aria-pressed={selectedArticleId === article.id}
                    onClick={() => selectArticle(article.id)}
                  >
                    <span className="inventory-article-copy">
                      <strong>{article.nombre}</strong>
                      <span>{article.categoria}</span>
                    </span>
                    <span className="inventory-unit">{article.unidad_medida}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="inventory-column">
          <section className="panel form-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">Registro de existencias</span>
                <h2>Registrar movimiento</h2>
              </div>
              <span className="step-mark">02</span>
            </div>
            <form onSubmit={handleCreateMovement}>
              <label className="field">
                <span>Artículo</span>
                <select
                  required
                  value={selectedArticleId}
                  disabled={articles.length === 0}
                  onChange={(event) => setSelectedArticleId(event.target.value)}
                >
                  <option value="">Seleccionar artículo</option>
                  {articles.map((article) => (
                    <option key={article.id} value={article.id}>{article.nombre}</option>
                  ))}
                </select>
              </label>
              <div className="field-row">
                <label className="field">
                  <span>Local</span>
                  <select
                    value={movementForm.local}
                    onChange={(event) => setMovementForm({
                      ...movementForm,
                      local: event.target.value as InventoryLocal,
                    })}
                  >
                    {inventoryLocals.map((local) => (
                      <option key={local} value={local}>{local}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Tipo</span>
                  <select
                    value={movementForm.tipo}
                    onChange={(event) => setMovementForm({
                      ...movementForm,
                      tipo: event.target.value as MovementType,
                    })}
                  >
                    {movementTypes.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="field-row">
                <label className="field">
                  <span>Cantidad</span>
                  <input
                    required
                    type="number"
                    step="any"
                    value={movementForm.cantidad}
                    onChange={(event) => setMovementForm({
                      ...movementForm,
                      cantidad: event.target.value,
                    })}
                  />
                </label>
                <label className="field">
                  <span>Autor</span>
                  <input
                    required
                    value={movementForm.autor}
                    onChange={(event) => setMovementForm({ ...movementForm, autor: event.target.value })}
                  />
                </label>
              </div>
              <div className="field-row">
                <label className="field">
                  <span>Fecha y hora</span>
                  <input
                    required
                    type="datetime-local"
                    value={movementForm.fecha}
                    onChange={(event) => setMovementForm({ ...movementForm, fecha: event.target.value })}
                  />
                </label>
                <label className="field">
                  <span>Motivo (opcional)</span>
                  <input
                    value={movementForm.motivo ?? ''}
                    onChange={(event) => setMovementForm({ ...movementForm, motivo: event.target.value })}
                  />
                </label>
              </div>
              <button
                className="primary-button"
                type="submit"
                disabled={savingMovement || articles.length === 0}
              >
                {savingMovement ? 'Guardando...' : 'Registrar movimiento'} <span>→</span>
              </button>
            </form>
          </section>

          <section className="panel list-panel">
            <div className="panel-heading list-heading">
              <div>
                <span className="section-kicker">Consulta derivada</span>
                <h2>Stock disponible</h2>
              </div>
            </div>
            <form className="inventory-stock-form" onSubmit={handleStockLookup}>
              <label className="field">
                <span>Artículo</span>
                <select
                  required
                  value={stockArticleId}
                  disabled={articles.length === 0}
                  onChange={(event) => {
                    setStockArticleId(event.target.value)
                    setStock(null)
                  }}
                >
                  <option value="">Seleccionar artículo</option>
                  {articles.map((article) => (
                    <option key={article.id} value={article.id}>{article.nombre}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Local</span>
                <select
                  value={stockLocal}
                  onChange={(event) => {
                    setStockLocal(event.target.value as InventoryLocal)
                    setStock(null)
                  }}
                >
                  {inventoryLocals.map((local) => (
                    <option key={local} value={local}>{local}</option>
                  ))}
                </select>
              </label>
              <button className="primary-button" type="submit" disabled={loadingStock || articles.length === 0}>
                {loadingStock ? 'Consultando...' : 'Consultar stock'} <span>→</span>
              </button>
            </form>
            {stock && (
              <div className="inventory-stock-result" aria-live="polite">
                <span className="section-kicker">{stock.local}</span>
                <div className="inventory-stock-value">
                  <strong>{stock.stock}</strong>
                  <span>{stock.unidad_medida}</span>
                </div>
                <span className="inventory-stock-article">
                  {articles.find((article) => article.id === stock.articulo_id)?.nombre ?? stock.articulo_id}
                </span>
              </div>
            )}
          </section>

          <section className="panel list-panel">
            <div className="panel-heading list-heading">
              <div>
                <span className="section-kicker">Solo lectura</span>
                <h2>Historial de movimientos</h2>
              </div>
              <span className="record-count">{movements.length} movimientos</span>
            </div>
            {loading ? (
              <p className="empty-state">Cargando movimientos...</p>
            ) : movements.length === 0 ? (
              <p className="empty-state">No hay movimientos registrados.</p>
            ) : (
              <div className="table-wrap">
                <table className="inventory-movement-table">
                  <thead>
                    <tr>
                      <th>Artículo</th>
                      <th>Local</th>
                      <th>Tipo</th>
                      <th>Cantidad</th>
                      <th>Autor</th>
                      <th>Fecha</th>
                      <th>Motivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {movements.map((movement) => (
                      <tr key={movement.id}>
                        <td className="strong-cell">
                          {articles.find((article) => article.id === movement.articulo_id)?.nombre ?? movement.articulo_id}
                        </td>
                        <td>{movement.local}</td>
                        <td>{movement.tipo}</td>
                        <td>{movement.cantidad}</td>
                        <td>{movement.autor}</td>
                        <td>{formatDate(movement.fecha)}</td>
                        <td>{movement.motivo || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}

export default InventoryManager