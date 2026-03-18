import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Link as LinkIcon, Upload, ArrowRight, X, FileVideo } from 'lucide-react';
import LanguagePicker from './LanguagePicker';
import { translateUrl, translateFile } from '../api';

const MAX_FILE_SIZE = 500 * 1024 * 1024;
const ACCEPTED_TYPES = ['.mp4', '.mov', '.webm', '.avi', '.mkv'];
const ACCEPTED_MIME = ['video/mp4', 'video/quicktime', 'video/webm', 'video/x-msvideo', 'video/x-matroska'];

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function Landing() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [mode, setMode] = useState('url');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  const [selectedLangs, setSelectedLangs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [shaking, setShaking] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const isValid = mode === 'url'
    ? url.trim().length > 0 && selectedLangs.length > 0
    : file !== null && selectedLangs.length > 0;

  const triggerShake = (msg) => {
    setError(msg);
    setShaking(true);
    setTimeout(() => setShaking(false), 600);
  };

  const handleFileDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);

    const droppedFile = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (!droppedFile) return;

    const ext = '.' + droppedFile.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext) && !ACCEPTED_MIME.includes(droppedFile.type)) {
      triggerShake(`Unsupported file type. Accepted: ${ACCEPTED_TYPES.join(', ')}`);
      return;
    }
    if (droppedFile.size > MAX_FILE_SIZE) {
      triggerShake('File too large. Maximum size is 500 MB.');
      return;
    }
    setFile(droppedFile);
    setError('');
  }, []);

  const handleSubmit = async () => {
    if (!isValid) return;
    setLoading(true);
    setError('');
    try {
      let data;
      if (mode === 'url') {
        data = await translateUrl(url.trim(), selectedLangs);
      } else {
        data = await translateFile(file, selectedLangs);
      }
      // Backend returns {job_ids: ["id1", "id2", ...], message: "..."}
      const jobIds = (data.job_ids || []).join(',');
      const jobsState = data.job_ids.map((id, i) => ({
        job_id: id,
        language: selectedLangs[i] || 'Unknown',
      }));
      navigate(`/progress/${jobIds}`, { state: { jobs: jobsState } });
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Translation request failed.';
      triggerShake(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Hero */}
      <motion.div
        style={styles.hero}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <h1 style={styles.headline}>
          Dub any video into{' '}
          <span style={styles.headlineAccent}>13+ languages</span>
        </h1>
        <p style={styles.subtitle}>
          Paste a link or upload a file. We handle transcription, translation,
          and voice synthesis — so your content speaks every language.
        </p>
      </motion.div>

      {/* Card */}
      <motion.div
        style={styles.card}
        className={shaking ? 'shake' : ''}
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Mode Toggle */}
        <div style={styles.toggleRow}>
          {['url', 'upload'].map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setError(''); }}
              style={{
                ...styles.toggleBtn,
                ...(mode === m ? styles.toggleActive : {}),
              }}
            >
              {m === 'url' ? (
                <><LinkIcon size={16} style={{ marginRight: 8 }} />Paste URL</>
              ) : (
                <><Upload size={16} style={{ marginRight: 8 }} />Upload File</>
              )}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <AnimatePresence mode="wait">
          {mode === 'url' ? (
            <motion.div
              key="url-input"
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 16 }}
              transition={{ duration: 0.25 }}
              style={styles.inputWrapper}
            >
              <LinkIcon size={18} style={styles.inputIcon} />
              <input
                type="url"
                value={url}
                onChange={(e) => { setUrl(e.target.value); setError(''); }}
                placeholder="https://youtube.com/watch?v=... or any video URL"
                style={styles.input}
              />
              {url && (
                <button
                  onClick={() => setUrl('')}
                  style={styles.clearBtn}
                  aria-label="Clear URL"
                >
                  <X size={16} />
                </button>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="file-input"
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              transition={{ duration: 0.25 }}
            >
              {!file ? (
                <div
                  style={{
                    ...styles.dropZone,
                    ...(dragOver ? styles.dropZoneActive : {}),
                  }}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleFileDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload size={32} style={{ color: 'var(--primary)', marginBottom: 12 }} />
                  <p style={styles.dropText}>
                    Drag & drop your video here, or <span style={styles.dropLink}>browse</span>
                  </p>
                  <p style={styles.dropHint}>
                    MP4, MOV, WebM, AVI, MKV — up to 500 MB
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_TYPES.join(',')}
                    onChange={handleFileDrop}
                    style={{ display: 'none' }}
                  />
                </div>
              ) : (
                <motion.div
                  style={styles.fileCard}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <FileVideo size={24} style={{ color: 'var(--secondary)', flexShrink: 0 }} />
                  <div style={styles.fileInfo}>
                    <span style={styles.fileName}>{file.name}</span>
                    <span style={styles.fileSize}>{formatSize(file.size)}</span>
                  </div>
                  <button
                    onClick={() => setFile(null)}
                    style={styles.fileRemove}
                    aria-label="Remove file"
                  >
                    <X size={16} />
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Language Picker */}
        <div style={{ marginTop: 28 }}>
          <LanguagePicker selected={selectedLangs} onSelect={setSelectedLangs} />
        </div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              style={styles.error}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Submit */}
        <motion.button
          onClick={handleSubmit}
          disabled={!isValid || loading}
          style={{
            ...styles.submitBtn,
            ...(!isValid || loading ? styles.submitDisabled : {}),
          }}
          whileHover={isValid && !loading ? { scale: 1.01 } : {}}
          whileTap={isValid && !loading ? { scale: 0.98 } : {}}
        >
          {loading ? (
            <span style={styles.spinner} />
          ) : (
            <>
              Translate
              <ArrowRight size={18} style={{ marginLeft: 8 }} />
            </>
          )}
        </motion.button>
      </motion.div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '720px',
    margin: '0 auto',
    padding: '40px 20px 80px',
  },
  hero: {
    textAlign: 'center',
    marginBottom: '48px',
  },
  headline: {
    fontSize: 'clamp(2rem, 5vw, 3.2rem)',
    fontWeight: 800,
    lineHeight: 1.15,
    letterSpacing: '-0.03em',
    color: 'var(--text)',
    marginBottom: '16px',
  },
  headlineAccent: {
    background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  subtitle: {
    fontSize: '1.1rem',
    color: 'var(--text-secondary)',
    maxWidth: '520px',
    margin: '0 auto',
    lineHeight: 1.6,
  },
  card: {
    background: 'rgba(20, 20, 31, 0.6)',
    backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: '32px',
  },
  toggleRow: {
    display: 'flex',
    gap: '4px',
    padding: '4px',
    background: 'var(--bg)',
    borderRadius: 'var(--radius-md)',
    marginBottom: '24px',
  },
  toggleBtn: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '12px 16px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '0.9rem',
    fontWeight: 600,
    color: 'var(--text-secondary)',
    transition: 'all var(--transition)',
  },
  toggleActive: {
    background: 'var(--surface)',
    color: 'var(--text)',
    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  inputIcon: {
    position: 'absolute',
    left: '16px',
    color: 'var(--text-secondary)',
    pointerEvents: 'none',
  },
  input: {
    width: '100%',
    padding: '16px 44px 16px 44px',
    fontSize: '1rem',
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text)',
    transition: 'border-color var(--transition), box-shadow var(--transition)',
  },
  clearBtn: {
    position: 'absolute',
    right: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    color: 'var(--text-secondary)',
    transition: 'color var(--transition)',
  },
  dropZone: {
    border: '2px dashed var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: '40px 24px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all var(--transition)',
  },
  dropZoneActive: {
    borderColor: 'var(--primary)',
    background: 'rgba(123, 97, 255, 0.05)',
  },
  dropText: {
    fontSize: '0.95rem',
    color: 'var(--text-secondary)',
    marginBottom: '8px',
  },
  dropLink: {
    color: 'var(--primary)',
    fontWeight: 600,
  },
  dropHint: {
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
    opacity: 0.6,
  },
  fileCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px',
    padding: '16px',
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
  },
  fileInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    minWidth: 0,
  },
  fileName: {
    fontSize: '0.9rem',
    fontWeight: 600,
    color: 'var(--text)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  fileSize: {
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
    fontFamily: 'var(--font-mono)',
  },
  fileRemove: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    color: 'var(--text-secondary)',
    flexShrink: 0,
    transition: 'color var(--transition), background var(--transition)',
  },
  error: {
    marginTop: '16px',
    padding: '12px 16px',
    background: 'rgba(255, 87, 87, 0.1)',
    border: '1px solid rgba(255, 87, 87, 0.3)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--error)',
    fontSize: '0.875rem',
    fontWeight: 500,
    overflow: 'hidden',
  },
  submitBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    marginTop: '24px',
    padding: '16px 24px',
    fontSize: '1rem',
    fontWeight: 700,
    color: '#fff',
    background: 'linear-gradient(135deg, var(--primary), #6246E5)',
    borderRadius: 'var(--radius-md)',
    boxShadow: '0 4px 20px var(--primary-glow)',
    transition: 'all var(--transition)',
    letterSpacing: '0.01em',
  },
  submitDisabled: {
    opacity: 0.4,
    cursor: 'not-allowed',
    boxShadow: 'none',
  },
  spinner: {
    display: 'inline-block',
    width: '20px',
    height: '20px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.6s linear infinite',
  },
};

// Inject spinner keyframe
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(style);
}
