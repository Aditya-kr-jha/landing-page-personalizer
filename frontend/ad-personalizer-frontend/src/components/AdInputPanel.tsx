import { useCallback, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image, Link, Monitor, Upload, X, FileImage } from 'lucide-react';
import type { AdInputMode } from '../types/api';

interface AdInputPanelProps {
  mode: AdInputMode;
  onModeChange: (mode: AdInputMode) => void;
  uploadedFile: File | null;
  onFileChange: (file: File | null) => void;
  adUrl: string;
  onAdUrlChange: (url: string) => void;
}

const MODES: { key: AdInputMode; label: string; icon: React.ReactNode }[] = [
  { key: 'upload', label: 'Upload Image', icon: <Upload size={13} strokeWidth={2} /> },
  { key: 'image_url', label: 'Image URL', icon: <Image size={13} strokeWidth={2} /> },
  { key: 'page_url', label: 'Ad Page URL', icon: <Monitor size={13} strokeWidth={2} /> },
];

export default function AdInputPanel({
  mode,
  onModeChange,
  uploadedFile,
  onFileChange,
  adUrl,
  onAdUrlChange,
}: AdInputPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith('image/')) return;
      onFileChange(file);
    },
    [onFileChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const previewUrl = uploadedFile ? URL.createObjectURL(uploadedFile) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <label
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--text-secondary)',
            letterSpacing: '0.01em',
            display: 'block',
            marginBottom: 10,
          }}
        >
          Ad Input
        </label>

        {/* Mode switcher */}
        <div
          style={{
            display: 'flex',
            gap: 4,
            padding: 4,
            background: 'var(--bg-surface-2)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border)',
            marginBottom: 14,
          }}
        >
          {MODES.map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => onModeChange(key)}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 5,
                padding: '7px 8px',
                borderRadius: 8,
                border: 'none',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 500,
                fontFamily: 'var(--font-sans)',
                transition: 'all var(--transition-fast)',
                position: 'relative',
                background: mode === key ? 'var(--bg-surface)' : 'transparent',
                color: mode === key ? 'var(--text-primary)' : 'var(--text-muted)',
                boxShadow: mode === key ? 'var(--shadow-xs)' : 'none',
              }}
            >
              {icon}
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      <AnimatePresence mode="wait">
        {mode === 'upload' && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
          >
            {uploadedFile && previewUrl ? (
              /* File preview */
              <div
                style={{
                  position: 'relative',
                  borderRadius: 'var(--radius-lg)',
                  overflow: 'hidden',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-surface-2)',
                }}
              >
                <img
                  src={previewUrl}
                  alt="Ad preview"
                  style={{
                    width: '100%',
                    height: 200,
                    objectFit: 'contain',
                    display: 'block',
                    padding: 12,
                  }}
                />
                <div
                  style={{
                    padding: '10px 14px',
                    borderTop: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 7,
                      fontSize: 13,
                      color: 'var(--text-secondary)',
                    }}
                  >
                    <FileImage size={14} />
                    {uploadedFile.name}
                  </span>
                  <button
                    className="btn-ghost"
                    onClick={() => onFileChange(null)}
                    style={{ padding: '4px 8px', fontSize: 12 }}
                  >
                    <X size={12} />
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              /* Drop zone */
              <div
                id="ad-upload-zone"
                onClick={() => fileInputRef.current?.click()}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                style={{
                  height: 200,
                  borderRadius: 'var(--radius-lg)',
                  border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border-strong)'}`,
                  background: dragging ? 'var(--accent-light)' : 'var(--bg-surface-2)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 10,
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 12,
                    background: dragging ? 'var(--accent)' : 'var(--bg-surface)',
                    border: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: dragging ? '#fff' : 'var(--text-secondary)',
                    transition: 'all var(--transition-fast)',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  <Upload size={20} strokeWidth={1.5} />
                </div>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)' }}>
                    Drop your ad image here
                  </p>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>
                    or{' '}
                    <span style={{ color: 'var(--accent)', textDecoration: 'underline' }}>
                      browse files
                    </span>
                    {' '}· PNG, JPG, WebP
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFile(file);
                    e.target.value = '';
                  }}
                />
              </div>
            )}
          </motion.div>
        )}

        {(mode === 'image_url' || mode === 'page_url') && (
          <motion.div
            key={mode}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
          >
            <div style={{ position: 'relative' }}>
              <span
                style={{
                  position: 'absolute',
                  left: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                  pointerEvents: 'none',
                }}
              >
                <Link size={15} />
              </span>
              <input
                id={`ad-${mode}-input`}
                type="url"
                className="input-field"
                placeholder={
                  mode === 'image_url'
                    ? 'https://cdn.example.com/ad-image.jpg'
                    : 'https://facebook.com/ads/library/...'
                }
                value={adUrl}
                onChange={(e) => onAdUrlChange(e.target.value)}
                style={{ paddingLeft: 38 }}
              />
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 7 }}>
              {mode === 'image_url'
                ? 'Direct URL to a publicly accessible ad image (PNG, JPG, WebP).'
                : 'URL of the page containing the ad (e.g., social media post).'}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
