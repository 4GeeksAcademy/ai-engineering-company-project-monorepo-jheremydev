import type { ReactNode } from 'react'

export default function Section({
  id,
  eyebrow,
  title,
  description,
  children,
}: {
  id?: string
  eyebrow: string
  title: string
  description?: string
  children: ReactNode
}) {
  return (
    <section className="site section" id={id}>
      <div className="section-head">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {children}
    </section>
  )
}
