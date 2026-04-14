

interface BeforeAfterTabProps {
  originalHtml: string;
  personalizedHtml: string;
}

export default function BeforeAfterTab({ originalHtml, personalizedHtml }: BeforeAfterTabProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
        Side-by-side comparison of the original and personalized landing page.
      </p>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 12,
        }}
      >
        {([
          { label: 'Original', html: originalHtml, id: 'original-frame', accent: false },
          { label: 'Personalized', html: personalizedHtml, id: 'personalized-frame', accent: true },
        ]).map(({ label, html, id, accent }) => (
          <div key={id} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div
              style={{
                padding: '7px 12px',
                borderRadius: 'var(--radius-sm)',
                background: accent ? 'var(--accent-light)' : 'var(--bg-surface-2)',
                border: `1px solid ${accent ? 'rgba(37,99,235,0.2)' : 'var(--border)'}`,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <span
                style={{
                  display: 'inline-block',
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: accent ? 'var(--accent)' : 'var(--text-muted)',
                }}
              />
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: accent ? 'var(--accent)' : 'var(--text-secondary)',
                }}
              >
                {label}
              </span>
            </div>
            <div
              style={{
                borderRadius: 'var(--radius-lg)',
                overflow: 'hidden',
                border: `1px solid ${accent ? 'rgba(37,99,235,0.2)' : 'var(--border)'}`,
                boxShadow: 'var(--shadow-sm)',
                background: '#fff',
              }}
            >
              <iframe
                id={id}
                srcDoc={html}
                title={label}
                sandbox="allow-same-origin"
                style={{ width: '100%', height: 520, border: 'none', display: 'block' }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
