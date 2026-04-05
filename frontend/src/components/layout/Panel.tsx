import type { ReactNode } from 'react'

interface PanelProps {
  title: string
  eyebrow?: string
  actions?: ReactNode
  children: ReactNode
}

export function Panel({ title, eyebrow, actions, children }: PanelProps) {
  return (
    <section className="panel">
      <header className="panel__header">
        <div>
          {eyebrow ? <p className="panel__eyebrow">{eyebrow}</p> : null}
          <h2 className="panel__title">{title}</h2>
        </div>
        {actions ? <div className="panel__actions">{actions}</div> : null}
      </header>
      <div className="panel__body">{children}</div>
    </section>
  )
}
