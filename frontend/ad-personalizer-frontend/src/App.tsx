import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Wand2 } from 'lucide-react';
import './index.css';

import type { AdInputMode, PersonalizeResponse } from './types/api';
import { personalize } from './api/personalize';

import Header from './components/Header';
import HeroSection from './components/HeroSection';
import AdInputPanel from './components/AdInputPanel';
import LandingPageInput from './components/LandingPageInput';
import LoadingState from './components/LoadingState';
import ResultTabs from './components/ResultTabs';
import Toast from './components/Toast';

type AppState = 'idle' | 'loading' | 'done' | 'error';

export default function App() {
  // ── Theme ────────────────────────────────────────────────────────────────────
  const [darkMode, setDarkMode] = useState(() => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  // ── Form state ───────────────────────────────────────────────────────────────
  const [adMode, setAdMode] = useState<AdInputMode>('upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [adUrl, setAdUrl] = useState('');
  const [landingPageUrl, setLandingPageUrl] = useState('');

  // ── App state ────────────────────────────────────────────────────────────────
  const [appState, setAppState] = useState<AppState>('idle');
  const [result, setResult] = useState<PersonalizeResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  // ── Validation ───────────────────────────────────────────────────────────────
  const isAdReady =
    (adMode === 'upload' && uploadedFile !== null) ||
    ((adMode === 'image_url' || adMode === 'page_url') && adUrl.trim().length > 0);

  const isLandingReady = landingPageUrl.trim().length > 0;
  const canSubmit = isAdReady && isLandingReady && appState !== 'loading';

  // ── Submit ───────────────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;
    setAppState('loading');
    setResult(null);
    setErrorMsg(null);

    const controller = new AbortController();
    abortRef.current = controller;

    // Scroll to loading indicator immediately
    setTimeout(() => {
      document.getElementById('loading-state-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    try {
      const data = await personalize({
        mode: adMode,
        uploadedFile,
        adUrl: adUrl.trim(),
        landingPageUrl: landingPageUrl.trim(),
        signal: controller.signal,
      });
      setResult(data);
      setAppState('done');
      // Scroll to results
      setTimeout(() => {
        document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    } catch (err: unknown) {
      if ((err as Error)?.name === 'AbortError') return;
      const message =
        (err as Error)?.message || 'An unexpected error occurred. Please try again.';
      setErrorMsg(message);
      setAppState('error');
    }
  }, [canSubmit, adMode, uploadedFile, adUrl, landingPageUrl]);

  // ── Keyboard shortcut ─────────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && canSubmit) {
        handleSubmit();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [canSubmit, handleSubmit]);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-base)', color: 'var(--text-primary)' }}>
      <Header darkMode={darkMode} onToggleDark={() => setDarkMode((d) => !d)} />

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '0 24px 80px' }}>
        {/* Hero */}
        <HeroSection />

        {/* ── Input Section ─────────────────────────────────────────────────── */}
        <section id="input-section" style={{ marginTop: 12 }}>
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.1 }}
          >
            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-2xl)',
                boxShadow: 'var(--shadow-lg)',
                padding: 28,
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 24,
              }}
            >
              {/* Left: Ad Input */}
              <div
                style={{
                  padding: 20,
                  background: 'var(--bg-surface-2)',
                  borderRadius: 'var(--radius-xl)',
                  border: '1px solid var(--border)',
                }}
              >
                <AdInputPanel
                  mode={adMode}
                  onModeChange={setAdMode}
                  uploadedFile={uploadedFile}
                  onFileChange={setUploadedFile}
                  adUrl={adUrl}
                  onAdUrlChange={setAdUrl}
                />
              </div>

              {/* Right: Landing Page Input */}
              <div
                style={{
                  padding: 20,
                  background: 'var(--bg-surface-2)',
                  borderRadius: 'var(--radius-xl)',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}
              >
                <LandingPageInput value={landingPageUrl} onChange={setLandingPageUrl} />

                {/* Hint */}
                <div
                  style={{
                    marginTop: 24,
                    padding: '14px 16px',
                    background: 'var(--accent-light)',
                    border: '1px solid rgba(37,99,235,0.18)',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  <p style={{ fontSize: 12.5, color: 'var(--accent)', lineHeight: 1.55 }}>
                    <strong>How it works:</strong> The AI analyzes your ad, scrapes the landing
                    page, generates targeted edits, and renders personalized HTML — all in under 30s.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* ── CTA Button ─────────────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            style={{ display: 'flex', justifyContent: 'center', marginTop: 20 }}
          >
            <button
              id="personalize-btn"
              className="btn-primary"
              onClick={handleSubmit}
              disabled={!canSubmit}
              style={{
                fontSize: 15,
                padding: '14px 36px',
                borderRadius: 'var(--radius-xl)',
                gap: 10,
                boxShadow: canSubmit ? '0 4px 24px var(--accent-glow)' : 'none',
                minWidth: 220,
              }}
            >
              {appState === 'loading' ? (
                <>
                  <motion.span
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, ease: 'linear', repeat: Infinity }}
                    style={{ display: 'flex' }}
                  >
                    <Loader2 size={18} strokeWidth={2} />
                  </motion.span>
                  Processing…
                </>
              ) : (
                <>
                  <Wand2 size={18} strokeWidth={2} />
                  Personalize Page
                  <span
                    style={{
                      fontSize: 12,
                      opacity: 0.7,
                      fontWeight: 400,
                      marginLeft: 4,
                    }}
                  >
                    ⌘↵
                  </span>
                </>
              )}
            </button>
          </motion.div>

          {!canSubmit && appState === 'idle' && (
            <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 10 }}>
              {!isAdReady && !isLandingReady
                ? 'Provide an ad input and a landing page URL to proceed.'
                : !isAdReady
                ? 'Upload an ad image or paste a URL to continue.'
                : 'Enter a landing page URL to continue.'}
            </p>
          )}
        </section>

        {/* ── Loading State ──────────────────────────────────────────────────── */}
        <AnimatePresence>
          {appState === 'loading' && (
            <motion.section
              key="loading"
              id="loading-state-section"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                marginTop: 32,
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-2xl)',
                boxShadow: 'var(--shadow-md)',
                overflow: 'hidden',
              }}
            >
              <LoadingState />
            </motion.section>
          )}
        </AnimatePresence>

        {/* ── Results ────────────────────────────────────────────────────────── */}
        <AnimatePresence>
          {appState === 'done' && result && (
            <motion.section
              key="results"
              style={{ marginTop: 32 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Results header bar */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 14,
                  padding: '0 4px',
                }}
              >
                <div>
                  <h2
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      letterSpacing: '-0.02em',
                    }}
                  >
                    Personalization Complete
                  </h2>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 3 }}>
                    {result.edits_applied.length} edit{result.edits_applied.length !== 1 ? 's' : ''} applied ·{' '}
                    {Math.round(result.confidence_score * 100)}% confidence ·{' '}
                    <span style={{ color: 'var(--text-secondary)' }}>{result.url}</span>
                  </p>
                </div>
                <button
                  id="personalize-again-btn"
                  className="btn-ghost"
                  onClick={() => {
                    setAppState('idle');
                    setResult(null);
                  }}
                >
                  Try Again
                </button>
              </div>

              <ResultTabs result={result} />
            </motion.section>
          )}
        </AnimatePresence>
      </main>

      {/* ── Toast ──────────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {errorMsg && (
          <Toast message={errorMsg} onDismiss={() => setErrorMsg(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
