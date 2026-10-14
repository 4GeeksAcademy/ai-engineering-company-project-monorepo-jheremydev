import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Stats from './components/Stats'
import Section from './components/Section'
import Departments from './components/Departments'
import Locations from './components/Locations'
import Footer from './components/Footer'
import './App.css'

function App() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Stats />
        <Section
          id="departamentos"
          eyebrow="Cómo trabajamos"
          title="Un equipo por cada parte del negocio"
          description="Catorce locales en dos países se sostienen en siete áreas que trabajan coordinadas desde Medellín y Miami."
        >
          <Departments />
        </Section>
        <Section
          id="locales"
          eyebrow="Dónde estamos"
          title="Dos países, una misma marca"
        >
          <Locations />
        </Section>
      </main>
      <Footer />
    </>
  )
}

export default App
