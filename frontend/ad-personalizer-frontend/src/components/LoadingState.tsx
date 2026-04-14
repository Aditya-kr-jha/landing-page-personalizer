import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Loader2 } from 'lucide-react';

const STEPS = [
  { id: 'ad', label: 'Analyzing Ad', duration: 4500 },
  { id: 'scrape', label: 'Scraping Page', duration: 3500 },
  { id: 'edits', label: 'Generating Edits', duration: 5000 },
  { id: 'render', label: 'Rendering HTML', duration: 3000 },
];

export default function LoadingState() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    let cumulative = 0;
    STEPS.forEach((step, i) => {
      cumulative += step.duration;
      timeout = setTimeout(() => {
        setActiveStep((prev) => Math.max(prev, i + 1));
      }, cumulative);
    });
    return () => clearTimeout(timeout);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.35 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '56px 24px',
        gap: 48,
      }}
    >
      {/* Animated spinner orb */}
      <div style={{ position: 'relative', width: 80, height: 80 }}>
        <svg
          width="80"
          height="80"
          viewBox="0 0 80 80"
          style={{ position: 'absolute', inset: 0 }}
        >
          <circle
            cx="40"
            cy="40"
            r="34"
            fill="none"
            stroke="var(--border)"
            strokeWidth="3"
          />
          <motion.circle
            cx="40"
            cy="40"
            r="34"
            fill="none"
            stroke="var(--accent)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="213.6"
            animate={{ strokeDashoffset: [213.6, 0] }}
            transition={{ duration: 16, ease: 'linear', repeat: Infinity }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, ease: 'linear', repeat: Infinity }}
          >
            <Loader2 size={26} color="var(--accent)" strokeWidth={2} />
          </motion.div>
        </div>
      </div>

      {/* Steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%', maxWidth: 360 }}>
        {STEPS.map((step, i) => {
          const done = activeStep > i;
          const current = activeStep === i;
          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                background: current
                  ? 'var(--accent-light)'
                  : done
                  ? 'var(--bg-surface-2)'
                  : 'transparent',
                border: `1px solid ${current ? 'rgba(37,99,235,0.2)' : done ? 'var(--border)' : 'transparent'}`,
                transition: 'all var(--transition-base)',
              }}
            >
              {/* Step icon */}
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  background: done
                    ? 'var(--success)'
                    : current
                    ? 'var(--accent)'
                    : 'var(--bg-surface-3)',
                  color: done || current ? '#fff' : 'var(--text-muted)',
                  transition: 'all var(--transition-base)',
                  fontSize: 11,
                  fontWeight: 700,
                }}
              >
                {done ? (
                  <Check size={14} strokeWidth={2.5} />
                ) : current ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, ease: 'linear', repeat: Infinity }}
                  >
                    <Loader2 size={14} strokeWidth={2.5} />
                  </motion.div>
                ) : (
                  <span>{i + 1}</span>
                )}
              </div>

              <span
                style={{
                  fontSize: 14,
                  fontWeight: current ? 600 : done ? 500 : 400,
                  color: current
                    ? 'var(--accent)'
                    : done
                    ? 'var(--text-secondary)'
                    : 'var(--text-muted)',
                  transition: 'color var(--transition-base)',
                }}
              >
                {step.label}
              </span>

              {done && (
                <AnimatePresence>
                  <motion.span
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={{
                      marginLeft: 'auto',
                      fontSize: 11,
                      fontWeight: 600,
                      color: 'var(--success)',
                    }}
                  >
                    Done
                  </motion.span>
                </AnimatePresence>
              )}
            </motion.div>
          );
        })}
      </div>

      <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
        This usually takes 20–30 seconds. Please don't close this tab.
      </p>
    </motion.div>
  );
}
