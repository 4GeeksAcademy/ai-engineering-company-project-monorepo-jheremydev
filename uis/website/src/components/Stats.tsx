const stats = [
  { value: '14', label: 'restaurantes propios' },
  { value: '2', label: 'países: Colombia y EE. UU.' },
  { value: '~115', label: 'personas en el equipo' },
  { value: '~$6M', label: 'facturación anual' },
]

export default function Stats() {
  return (
    <div className="site">
      <div className="stats">
        {stats.map((stat) => (
          <div className="stat-card" key={stat.label}>
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
