import { useRef } from 'react';
import { Download, Copy, ExternalLink } from 'lucide-react';

interface PreviewTabProps {
  html: string;
  label?: string;
}

export default function PreviewTab({ html, label = 'Personalized Page' }: PreviewTabProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(html);
  };

  const handleDownload = () => {
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'personalized-page.html';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleOpenInTab = () => {
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 14px',
          background: 'var(--bg-surface-2)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border)',
        }}
      >
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)' }}>
          {label}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button id="copy-html-btn" className="btn-ghost" onClick={handleCopy} style={{ padding: '5px 10px', fontSize: 12 }}>
            <Copy size={12} />
            Copy HTML
          </button>
          <button id="download-html-btn" className="btn-ghost" onClick={handleDownload} style={{ padding: '5px 10px', fontSize: 12 }}>
            <Download size={12} />
            Download
          </button>
          <button id="open-tab-btn" className="btn-ghost" onClick={handleOpenInTab} style={{ padding: '5px 10px', fontSize: 12 }}>
            <ExternalLink size={12} />
            Open
          </button>
        </div>
      </div>

      {/* iframe */}
      <div
        style={{
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-md)',
          background: '#fff',
        }}
      >
        <iframe
          ref={iframeRef}
          id="personalized-preview-frame"
          srcDoc={html}
          title={label}
          sandbox="allow-same-origin"
          style={{
            width: '100%',
            height: 600,
            border: 'none',
            display: 'block',
          }}
        />
      </div>
    </div>
  );
}
