const departments = [
  { name: 'Operaciones de Restaurante', lead: 'Felipe Guerrero', description: 'Supervisa los 14 locales en los dos países, con equipos de cocina y servicio propios en cada uno.' },
  { name: 'Compras y Proveedores', lead: 'Lucía Fernández', description: 'Gestiona la relación con cerca de 20 proveedores de materia prima, embalaje y limpieza.' },
  { name: 'Marketing y Experiencia Digital', lead: 'Camila Ospina', description: 'Cuida cómo Brasaland se presenta a sus clientes: web, redes, programa de fidelización.' },
  { name: 'Personas y Cultura', lead: 'Ashley Turner', description: 'Contratos, horarios y onboarding para las ~115 personas del equipo en dos mercados laborales.' },
  { name: 'Formación y Estándares de Calidad', lead: 'Jake Morrison', description: 'Garantiza que cada plato se prepare y se sirva igual en cualquier local, en cualquier país.' },
  { name: 'Tecnología', lead: 'Nicolás Park (CTO)', description: 'Construye las herramientas internas que permiten operar con datos reales, no con intuición.' },
]

export default function Departments() {
  return (
    <div className="dept-grid">
      {departments.map((dept) => (
        <div className="dept-card" key={dept.name}>
          <h3>{dept.name}</h3>
          <p>{dept.description}</p>
          <span>{dept.lead}</span>
        </div>
      ))}
    </div>
  )
}
