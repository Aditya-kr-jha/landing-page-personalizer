import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, XCircle } from 'lucide-react';
import type { AppliedEdit, SkippedEdit } from '../../types/api';

interface EditsTabProps {
  editsApplied: AppliedEdit[];
  editsSkipped: SkippedEdit[];
}

function EditTypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    headline: 'var(--accent)',
    subheadline: '#7c3aed',
    cta: '#d97706',
    body: '#059669',
    section: '#0891b2',
  };
  const color = colors[type.toLowerCase()] ?? 'var(--text-muted)';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 100,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.03em',
        textTransform: 'uppercase',
        background: `${color}18`,
        color,
        border: `1px solid ${color}30`,
      }}
    >
      {type}
    </span>
  );
}

export default function EditsTab({ editsApplied, editsSkipped }: EditsTabProps) {
  const total = editsApplied.length + editsSkipped.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Summary row */}
      <div style={{ display: 'flex', gap: 10 }}>
        <div
          style={{
            flex: 1,
            padding: '12px 16px',
            background: 'rgba(22, 163, 74, 0.08)',
            border: '1px solid rgba(22, 163, 74, 0.2)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <CheckCircle2 size={17} color="var(--success)" />
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
              {editsApplied.length}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Applied</div>
          </div>
        </div>
        <div
          style={{
            flex: 1,
            padding: '12px 16px',
            background: 'rgba(220, 38, 38, 0.07)',
            border: '1px solid rgba(220, 38, 38, 0.18)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <XCircle size={17} color="var(--danger)" />
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
              {editsSkipped.length}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Skipped</div>
          </div>
        </div>
        <div
          style={{
            flex: 1,
            padding: '12px 16px',
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
              {total}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Total Edits</div>
          </div>
        </div>
      </div>

      {/* Applied edits */}
      {editsApplied.length > 0 && (
        <div>
          <h3
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: 10,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <CheckCircle2 size={14} color="var(--success)" />
            Applied Edits
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {editsApplied.map((edit, i) => (
              <motion.div
                key={`${edit.section_id}-${i}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                style={{
                  padding: '14px 16px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                {/* Header row */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 12,
                  }}
                >
                  <code
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: 'var(--text-secondary)',
                      background: 'var(--bg-surface-2)',
                      padding: '2px 7px',
                      borderRadius: 6,
                      border: '1px solid var(--border)',
                    }}
                  >
                    {edit.section_id}
                  </code>
                  <EditTypeBadge type={edit.edit_type} />
                  <span
                    style={{
                      marginLeft: 'auto',
                      fontSize: 11,
                      color: 'var(--text-muted)',
                    }}
                  >
                    {edit.match_type} · {Math.round(edit.confidence * 100)}% confidence
                  </span>
                </div>

                {/* Before → After */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <div
                    style={{
                      flex: 1,
                      padding: '10px 12px',
                      background: 'rgba(220, 38, 38, 0.05)',
                      border: '1px solid rgba(220, 38, 38, 0.15)',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--danger)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Before
                    </p>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {edit.original_text}
                    </p>
                  </div>
                  <ArrowRight size={16} color="var(--text-muted)" style={{ marginTop: 28, flexShrink: 0 }} />
                  <div
                    style={{
                      flex: 1,
                      padding: '10px 12px',
                      background: 'rgba(22, 163, 74, 0.06)',
                      border: '1px solid rgba(22, 163, 74, 0.18)',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--success)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      After
                    </p>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {edit.replacement_text}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Skipped edits */}
      {editsSkipped.length > 0 && (
        <div>
          <h3
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--text-secondary)',
              marginBottom: 10,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <XCircle size={14} color="var(--danger)" />
            Skipped Edits
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {editsSkipped.map((edit, i) => (
              <div
                key={`${edit.section_id}-${i}`}
                style={{
                  padding: '12px 14px',
                  background: 'rgba(220, 38, 38, 0.04)',
                  border: '1px solid rgba(220, 38, 38, 0.14)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 10,
                }}
              >
                <code
                  style={{
                    fontSize: 12,
                    color: 'var(--text-secondary)',
                    background: 'var(--bg-surface)',
                    padding: '2px 7px',
                    borderRadius: 6,
                    border: '1px solid var(--border)',
                    flexShrink: 0,
                  }}
                >
                  {edit.section_id}
                </code>
                <EditTypeBadge type={edit.edit_type} />
                <span style={{ fontSize: 13, color: 'var(--danger)', marginLeft: 4 }}>
                  {edit.reason}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
