import { motion } from 'framer-motion';
import { ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import type { GuardrailResult } from '../../types/api';

interface MetricsTabProps {
  confidenceScore: number;
  warnings: string[];
  guardrailResult: GuardrailResult;
}

const SEVERITY_COLOR: Record<string, string> = {
  info: 'var(--accent)',
  warning: 'var(--warning)',
  critical: 'var(--danger)',
};

const SEVERITY_BG: Record<string, string> = {
  info: 'rgba(37, 99, 235, 0.07)',
  warning: 'rgba(217, 119, 6, 0.07)',
  critical: 'rgba(220, 38, 38, 0.07)',
};

const CHECK_LABELS: Record<string, string> = {
  fact_check: 'Fact Check',
  scope_check: 'Scope Check',
  schema_check: 'Schema Check',
  html_safety_check: 'HTML Safety',
};

function ConfidenceGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--danger)';

  return (
    <div
      style={{
        padding: '24px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-sm)',
        display: 'flex',
        alignItems: 'center',
        gap: 24,
      }}
    >
      {/* Circular gauge */}
      <div style={{ position: 'relative', width: 100, height: 100, flexShrink: 0 }}>
        <svg width="100" height="100" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="50" cy="50" r="40" fill="none" stroke="var(--bg-surface-3)" strokeWidth="8" />
          <motion.circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 40}`}
            initial={{ strokeDashoffset: 2 * Math.PI * 40 }}
            animate={{ strokeDashoffset: 2 * Math.PI * 40 * (1 - score) }}
            transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
          }}
        >
          <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
            {pct}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>/ 100</span>
        </div>
      </div>

      <div>
        <p style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
          Overall Confidence
        </p>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, maxWidth: 260 }}>
          {pct >= 80
            ? 'High confidence. The personalized page closely aligns with the ad message.'
            : pct >= 60
            ? 'Moderate confidence. Some sections may have partial alignment.'
            : 'Low confidence. Review edits and warnings carefully before deploying.'}
        </p>
        {/* Bar */}
        <div style={{ marginTop: 14, height: 6, borderRadius: 100, background: 'var(--bg-surface-3)', overflow: 'hidden', maxWidth: 280 }}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.9, ease: 'easeOut', delay: 0.3 }}
            style={{ height: '100%', background: color, borderRadius: 100 }}
          />
        </div>
      </div>
    </div>
  );
}

export default function MetricsTab({ confidenceScore, warnings, guardrailResult }: MetricsTabProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Confidence */}
      <ConfidenceGauge score={confidenceScore} />

      {/* Guardrail Results */}
      <div
        style={{
          padding: '20px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          {guardrailResult.overall_passed ? (
            <ShieldCheck size={18} color="var(--success)" />
          ) : (
            <ShieldAlert size={18} color="var(--danger)" />
          )}
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
            Guardrail Checks
          </span>
          <span
            style={{
              marginLeft: 'auto',
              fontSize: 12,
              fontWeight: 600,
              color: guardrailResult.overall_passed ? 'var(--success)' : 'var(--danger)',
              background: guardrailResult.overall_passed
                ? 'rgba(22, 163, 74, 0.1)'
                : 'rgba(220, 38, 38, 0.08)',
              border: `1px solid ${guardrailResult.overall_passed ? 'rgba(22, 163, 74, 0.25)' : 'rgba(220, 38, 38, 0.2)'}`,
              padding: '3px 10px',
              borderRadius: 100,
            }}
          >
            {guardrailResult.overall_passed ? 'All Passed' : 'Checks Failed'}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {guardrailResult.checks.map((check) => (
            <div
              key={check.check_name}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 12px',
                background: check.passed ? 'rgba(22, 163, 74, 0.05)' : 'rgba(220, 38, 38, 0.05)',
                border: `1px solid ${check.passed ? 'rgba(22, 163, 74, 0.15)' : 'rgba(220, 38, 38, 0.15)'}`,
                borderRadius: 'var(--radius-md)',
              }}
            >
              {check.passed ? (
                <CheckCircle2 size={15} color="var(--success)" />
              ) : (
                <XCircle size={15} color="var(--danger)" />
              )}
              <div>
                <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {CHECK_LABELS[check.check_name] ?? check.check_name}
                </p>
                {check.blocked_section_ids.length > 0 && (
                  <p style={{ fontSize: 11, color: 'var(--danger)', marginTop: 2 }}>
                    Blocked: {check.blocked_section_ids.join(', ')}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Guardrail Warnings */}
      {guardrailResult.all_warnings?.length > 0 && (
        <div
          style={{
            padding: '20px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-xl)',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <AlertTriangle size={16} color="var(--warning)" />
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              Guardrail Warnings ({guardrailResult.all_warnings.length})
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {guardrailResult.all_warnings.map((w, i) => (
              <div
                key={i}
                style={{
                  padding: '10px 12px',
                  background: SEVERITY_BG[w.severity] || 'var(--bg-surface-2)',
                  borderLeft: `3px solid ${SEVERITY_COLOR[w.severity] || 'var(--border)'}`,
                  borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      color: SEVERITY_COLOR[w.severity],
                    }}
                  >
                    {w.severity}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {CHECK_LABELS[w.check_name] ?? w.check_name}
                    {w.section_id ? ` · ${w.section_id}` : ''}
                  </span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {w.message}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* General Warnings */}
      {warnings.length > 0 && (
        <div
          style={{
            padding: '16px',
            background: 'rgba(217, 119, 6, 0.06)',
            border: '1px solid rgba(217, 119, 6, 0.2)',
            borderRadius: 'var(--radius-xl)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <AlertTriangle size={15} color="var(--warning)" />
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--warning)' }}>
              Pipeline Warnings
            </span>
          </div>
          <ul style={{ paddingLeft: 18, margin: 0 }}>
            {warnings.map((w, i) => (
              <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 5 }}>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
