import { Globe } from 'lucide-react';

interface LandingPageInputProps {
  value: string;
  onChange: (v: string) => void;
}

export default function LandingPageInput({ value, onChange }: LandingPageInputProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <label
        htmlFor="landing-page-url"
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--text-secondary)',
          letterSpacing: '0.01em',
        }}
      >
        Landing Page URL
      </label>
      <div style={{ position: 'relative' }}>
        <span
          style={{
            position: 'absolute',
            left: 13,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)',
            pointerEvents: 'none',
          }}
        >
          <Globe size={15} />
        </span>
        <input
          id="landing-page-url"
          type="url"
          className="input-field"
          placeholder="https://your-landing-page.com"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={{ paddingLeft: 38 }}
        />
      </div>
      <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
        The public URL of the landing page you want to personalize. Must be publicly accessible.
      </p>
    </div>
  );
}
