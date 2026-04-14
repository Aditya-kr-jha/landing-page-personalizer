import { motion } from 'framer-motion';
import { ArrowDown, Sparkles } from 'lucide-react';

export default function HeroSection() {
  return (
    <section
      id="hero"
      style={{
        position: 'relative',
        padding: '96px 24px 80px',
        textAlign: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Dot grid background */}
      <div
        className="dot-grid"
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.5,
          zIndex: 0,
        }}
      />

      {/* Gradient orb */}
      <div
        className="hero-gradient"
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
        }}
      />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 720, margin: '0 auto' }}>
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '5px 12px',
              background: 'var(--accent-light)',
              color: 'var(--accent)',
              border: '1px solid rgba(37, 99, 235, 0.2)',
              borderRadius: 100,
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: '0.02em',
              marginBottom: 28,
            }}
          >
            <Sparkles size={12} />
            Powered by GPT
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut', delay: 0.08 }}
          style={{
            fontSize: 'clamp(36px, 5vw, 58px)',
            fontWeight: 800,
            lineHeight: 1.1,
            letterSpacing: '-0.035em',
            color: 'var(--text-primary)',
            marginBottom: 20,
          }}
        >
          Turn Your Ads Into{' '}
          <span
            style={{
              background: 'linear-gradient(135deg, var(--accent) 0%, #818cf8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            High-Converting
          </span>{' '}
          Landing Pages
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut', delay: 0.16 }}
          style={{
            fontSize: 18,
            color: 'var(--text-secondary)',
            lineHeight: 1.65,
            maxWidth: 560,
            margin: '0 auto 36px',
          }}
        >
          Instantly personalize any landing page to match your ad's messaging
          using AI. Fix message mismatch. Eliminate conversion leak.
        </motion.p>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut', delay: 0.24 }}
        >
          <a
            href="#input-section"
            className="btn-primary"
            id="hero-cta"
            style={{ fontSize: 15, padding: '12px 28px', borderRadius: 'var(--radius-lg)' }}
          >
            Try It Now
            <ArrowDown size={16} />
          </a>
        </motion.div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.4 }}
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 40,
            marginTop: 56,
          }}
        >
          {[
            { value: '4-step', label: 'AI Pipeline' },
            { value: 'GPT-5.4', label: 'Vision Model' },
            { value: '<30s', label: 'Per Page' },
          ].map((stat) => (
            <div key={stat.label} style={{ textAlign: 'center' }}>
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                  color: 'var(--text-primary)',
                }}
              >
                {stat.value}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
