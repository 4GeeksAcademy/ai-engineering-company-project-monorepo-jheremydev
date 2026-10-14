export default function Navbar() {
  return (
    <header className="navbar">
      <div className="site navbar-inner">
        <a className="brand" href="#top">Brasaland</a>
        <nav>
          <ul className="nav-links">
            <li><a href="#departamentos">Cómo trabajamos</a></li>
            <li><a href="#locales">Dónde estamos</a></li>
            <li><a href="#contacto">Contacto</a></li>
          </ul>
        </nav>
      </div>
    </header>
  )
}
