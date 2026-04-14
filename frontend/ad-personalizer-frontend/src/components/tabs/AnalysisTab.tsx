import { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { AdAnalysis, PageAnalysis } from '../../types/api';

interface AnalysisTabProps {
  adAnalysis: AdAnalysis;
  pageAnalysis: PageAnalysis;
}

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre
      style={{
        padding: '16px',
        background: 'var(--bg-surface-2)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        fontSize: 12.5,
        lineHeight: 1.7,
        color: 'var(--text-secondary)',
        overflowX: 'auto',
        fontFamily: "'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace",
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function Collapsible({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div
      style={{
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        background: 'var(--bg-surface)',
      }}
    >
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: '100%',
          padding: '14px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          cursor: 'pointer',
          background: 'none',
          border: 'none',
          fontFamily: 'var(--font-sans)',
          textAlign: 'left',
          borderBottom: open ? '1px solid var(--border)' : 'none',
          transition: 'background var(--transition-fast)',
        }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-surface-2)')}
        onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = 'none')}
      >
        {open ? (
          <ChevronDown size={16} color="var(--text-muted)" />
        ) : (
          <ChevronRight size={16} color="var(--text-muted)" />
        )}
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{title}</span>
      </button>

      {open && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
          style={{ padding: 16 }}
        >
          {children}
        </motion.div>
      )}
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 12,
        padding: '10px 0',
        borderBottom: '1px solid var(--border)',
        alignItems: 'flex-start',
      }}
    >
      <span
        style={{
          minWidth: 160,
          fontSize: 12,
          fontWeight: 600,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          paddingTop: 1,
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.55, flex: 1 }}>
        {value}
      </span>
    </div>
  );
}

function ToneBadge({ tone }: { tone: string }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        padding: '2px 8px',
        borderRadius: 100,
        fontSize: 11,
        fontWeight: 600,
        background: 'var(--accent-light)',
        color: 'var(--accent)',
        border: '1px solid rgba(37,99,235,0.2)',
        marginRight: 4,
        marginBottom: 4,
        textTransform: 'capitalize',
      }}
    >
      {tone}
    </span>
  );
}

export default function AnalysisTab({ adAnalysis, pageAnalysis }: AnalysisTabProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Ad Analysis */}
      <Collapsible title="Ad Analysis" defaultOpen>
        <div>
          <FieldRow label="Headline" value={adAnalysis.headline} />
          <FieldRow label="Offer" value={adAnalysis.offer ?? '—'} />
          <FieldRow label="Value Proposition" value={adAnalysis.value_proposition} />
          <FieldRow label="Product / Service" value={adAnalysis.product_or_service ?? '—'} />
          <FieldRow label="Target Audience" value={adAnalysis.target_audience} />
          <FieldRow
            label="Pain Points"
            value={
              adAnalysis.audience_pain_points.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {adAnalysis.audience_pain_points.map((p, i) => (
                    <li key={i} style={{ marginBottom: 3 }}>{p}</li>
                  ))}
                </ul>
              ) : (
                '—'
              )
            }
          />
          <FieldRow
            label="Primary Tone"
            value={<ToneBadge tone={adAnalysis.tone} />}
          />
          <FieldRow
            label="Secondary Tones"
            value={
              adAnalysis.secondary_tones.length > 0 ? (
                <div>{adAnalysis.secondary_tones.map((t) => <ToneBadge key={t} tone={t} />)}</div>
              ) : (
                '—'
              )
            }
          />
          <FieldRow label="CTA Text" value={adAnalysis.cta_text ?? '—'} />
          <FieldRow label="CTA Urgency" value={adAnalysis.cta_urgency} />
          <FieldRow
            label="Key Phrases"
            value={
              adAnalysis.key_phrases.length > 0
                ? adAnalysis.key_phrases.join(', ')
                : '—'
            }
          />
          <FieldRow label="Trust Signals" value={adAnalysis.trust_signals.join(', ') || '—'} />
          <FieldRow label="Brand Voice" value={adAnalysis.brand_voice_notes ?? '—'} />
          <FieldRow label="Confidence" value={`${Math.round(adAnalysis.confidence * 100)}%`} />
        </div>
      </Collapsible>

      {/* Page Analysis */}
      <Collapsible title="Page Analysis" defaultOpen>
        <div>
          <FieldRow
            label="Overall Score"
            value={
              <span style={{ fontWeight: 700, color: 'var(--accent)' }}>
                {Math.round(pageAnalysis.overall_score * 10) / 10} / 10
              </span>
            }
          />
          <FieldRow
            label="Summary"
            value={pageAnalysis.summary ?? '—'}
          />
          <FieldRow
            label="Weaknesses"
            value={
              pageAnalysis.identified_weaknesses.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {pageAnalysis.identified_weaknesses.map((w, i) => (
                    <li key={i} style={{ marginBottom: 3, color: 'var(--danger)' }}>{w}</li>
                  ))}
                </ul>
              ) : (
                'None identified'
              )
            }
          />
          <FieldRow
            label="Recommendations"
            value={
              pageAnalysis.recommendations.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {pageAnalysis.recommendations.map((r, i) => (
                    <li key={i} style={{ marginBottom: 3 }}>{r}</li>
                  ))}
                </ul>
              ) : (
                '—'
              )
            }
          />
        </div>
        {/* Section scores */}
        {pageAnalysis.section_scores?.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 10 }}>
              Section Scores
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {pageAnalysis.section_scores.map((s) => (
                <div key={s.section_id} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                    <code style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{s.section_id}</code>
                    <span style={{ color: 'var(--text-muted)' }}>{s.score}/10</span>
                  </div>
                  <div style={{ height: 5, borderRadius: 100, background: 'var(--bg-surface-3)', overflow: 'hidden' }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(s.score / 10) * 100}%` }}
                      transition={{ duration: 0.6, ease: 'easeOut' }}
                      style={{ height: '100%', background: 'var(--accent)', borderRadius: 100 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Collapsible>

      {/* Raw JSON fallback */}
      <Collapsible title="Raw JSON — Ad Analysis">
        <JsonBlock data={adAnalysis} />
      </Collapsible>
      <Collapsible title="Raw JSON — Page Analysis">
        <JsonBlock data={pageAnalysis} />
      </Collapsible>
    </div>
  );
}
