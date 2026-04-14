import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle } from 'lucide-react';

interface ToastProps {
  message: string;
  onDismiss: () => void;
}

export default function Toast({ message, onDismiss }: ToastProps) {
  return (
    <AnimatePresence>
      <motion.div
        id="error-toast"
        initial={{ opacity: 0, x: 48, y: 0 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 48 }}
        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
        style={{
          position: 'fixed',
          bottom: 28,
          right: 28,
          zIndex: 100,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 12,
          padding: '14px 16px',
          background: 'var(--bg-surface)',
          border: '1px solid rgba(220, 38, 38, 0.25)',
          borderLeft: '3px solid var(--danger)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-xl)',
          maxWidth: 380,
          minWidth: 280,
        }}
      >
        <AlertCircle
          size={18}
          color="var(--danger)"
          strokeWidth={2}
          style={{ flexShrink: 0, marginTop: 1 }}
        />
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>
            Error
          </p>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{message}</p>
        </div>
        <button
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            padding: 2,
            flexShrink: 0,
          }}
          aria-label="Dismiss error"
        >
          <X size={15} />
        </button>
      </motion.div>
    </AnimatePresence>
  );
}
