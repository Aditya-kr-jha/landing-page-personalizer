import { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, SplitSquareHorizontal, FileEdit, BarChart2, ShieldCheck } from 'lucide-react';
import type { PersonalizeResponse } from '../types/api';
import PreviewTab from './tabs/PreviewTab';
import BeforeAfterTab from './tabs/BeforeAfterTab';
import EditsTab from './tabs/EditsTab';
import AnalysisTab from './tabs/AnalysisTab';
import MetricsTab from './tabs/MetricsTab';

interface ResultTabsProps {
  result: PersonalizeResponse;
}

type TabKey = 'preview' | 'before_after' | 'edits' | 'analysis' | 'metrics';

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: 'preview', label: 'Preview', icon: <Eye size={14} /> },
  { key: 'before_after', label: 'Before vs After', icon: <SplitSquareHorizontal size={14} /> },
  { key: 'edits', label: 'Edits', icon: <FileEdit size={14} /> },
  { key: 'analysis', label: 'Analysis', icon: <BarChart2 size={14} /> },
  { key: 'metrics', label: 'Metrics', icon: <ShieldCheck size={14} /> },
];

export default function ResultTabs({ result }: ResultTabsProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('preview');

  return (
    <motion.div
      id="results-section"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-2xl)',
        boxShadow: 'var(--shadow-lg)',
        overflow: 'hidden',
      }}
    >
      {/* Tab bar */}
      <div
        style={{
          borderBottom: '1px solid var(--border)',
          padding: '0 20px',
          display: 'flex',
          alignItems: 'flex-end',
          gap: 2,
          overflowX: 'auto',
        }}
      >
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              id={`tab-${tab.key}`}
              onClick={() => setActiveTab(tab.key)}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '12px 14px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                color: active ? 'var(--text-primary)' : 'var(--text-muted)',
                transition: 'color var(--transition-fast)',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => {
                if (!active) (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)';
              }}
              onMouseLeave={(e) => {
                if (!active) (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
              }}
            >
              {tab.icon}
              {tab.label}
              {/* Animated underline */}
              {active && (
                <motion.span
                  layoutId="tab-underline"
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: 2,
                    background: 'var(--accent)',
                    borderRadius: '2px 2px 0 0',
                  }}
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div style={{ padding: 20 }}>
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
        >
          {activeTab === 'preview' && (
            <PreviewTab html={result.personalized_html} />
          )}
          {activeTab === 'before_after' && (
            <BeforeAfterTab
              originalHtml={result.original_html}
              personalizedHtml={result.personalized_html}
            />
          )}
          {activeTab === 'edits' && (
            <EditsTab
              editsApplied={result.edits_applied}
              editsSkipped={result.edits_skipped}
            />
          )}
          {activeTab === 'analysis' && (
            <AnalysisTab
              adAnalysis={result.ad_analysis}
              pageAnalysis={result.page_analysis}
            />
          )}
          {activeTab === 'metrics' && (
            <MetricsTab
              confidenceScore={result.confidence_score}
              warnings={result.warnings}
              guardrailResult={result.guardrail_result}
            />
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}
