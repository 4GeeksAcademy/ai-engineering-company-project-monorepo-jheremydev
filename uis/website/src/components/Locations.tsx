const locations = [
  { name: 'Medellín, Colombia', description: 'Sede central de Brasaland, donde nació la marca en 2008 y desde donde opera la Dirección Ejecutiva y Tecnología.' },
  { name: 'Miami, Florida (EE. UU.)', description: 'Oficina comercial y de operaciones que coordina los locales de Florida.' },
]

export default function Locations() {
  return (
    <div className="locations">
      {locations.map((location) => (
        <div className="location-card" key={location.name}>
          <h3>{location.name}</h3>
          <p>{location.description}</p>
        </div>
      ))}
    </div>
  )
}
