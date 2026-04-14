import { Moon, Sun, Zap } from 'lucide-react';

interface HeaderProps {
  darkMode: boolean;
  onToggleDark: () => void;
}

export default function Header({ darkMode, onToggleDark }: HeaderProps) {
  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        background: darkMode
          ? 'rgba(9, 9, 11, 0.8)'
          : 'rgba(250, 250, 250, 0.85)',
        borderBottom: '1px solid var(--border)',
        transition: 'background var(--transition-slow)',
      }}
    >
      <div
        style={{
          maxWidth: 1100,
          margin: '0 auto',
          padding: '0 24px',
          height: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Logo */}
        <a
          href="#"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            textDecoration: 'none',
          }}
        >
          <span
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 30,
              height: 30,
              background: 'var(--accent)',
              borderRadius: 8,
              color: '#fff',
            }}
          >
            <Zap size={16} strokeWidth={2.5} />
          </span>
          <span
            style={{
              fontWeight: 700,
              fontSize: 16,
              letterSpacing: '-0.02em',
              color: 'var(--text-primary)',
            }}
          >
            AdPersonalizer
          </span>
          <span
            className="tag"
            style={{ marginLeft: 2 }}
          >
            Beta
          </span>
        </a>

        {/* Right actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span
            style={{
              fontSize: 13,
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <span
              style={{
                display: 'inline-block',
                width: 7,
                height: 7,
                background: '#16a34a',
                borderRadius: '50%',
                boxShadow: '0 0 0 2px rgba(22, 163, 74, 0.25)',
              }}
            />
            API Live
          </span>
          <button
            id="dark-mode-toggle"
            className="btn-ghost"
            onClick={onToggleDark}
            aria-label="Toggle dark mode"
            style={{ padding: '6px 10px' }}
          >
            {darkMode ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </div>
    </header>
  );
}
