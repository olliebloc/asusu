import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Copy, Download, ArrowLeft, Check, Play } from 'lucide-react';
import { getJobStatus } from '../api';

export default function ResultPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  // Support multiple job IDs (comma-separated)
  const jobIds = id.includes(',') ? id.split(',').filter(Boolean) : [id];
  const [activeTab, setActiveTab] = useState(0);
  const [allJobs, setAllJobs] = useState([]);

  useEffect(() => {
    async function fetchJobs() {
      setLoading(true);
      setError('');
      try {
        const results = await Promise.all(jobIds.map((jid) => getJobStatus(jid)));
        setAllJobs(results);
        setJob(results[0]);
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to load video.');
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, [id]);

  const activeJob = allJobs[activeTab] || job;
  // Backend JobStatus puts the video URL in result.url on SUCCESS
  const videoUrl = activeJob?.result?.url || activeJob?.result_url || '';
  const language = activeJob?.result?.target_lang || activeJob?.language || 'Translated';

  const handleCopy = () => {
    const url = videoUrl || window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleDownload = () => {
    if (!videoUrl) return;
    const a = document.createElement('a');
    a.href = videoUrl;
    a.download = `asusu-${language.toLowerCase()}.mp4`;
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingWrapper}>
          <motion.div
            style={styles.loadingOrb}
            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          <p style={styles.loadingText}>Loading video...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <motion.div
          style={styles.errorCard}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p style={styles.errorText}>{error}</p>
          <button onClick={() => navigate('/')} style={styles.primaryBtn}>
            <ArrowLeft size={16} style={{ marginRight: 8 }} />
            Translate Another
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Language Tabs */}
        {allJobs.length > 1 && (
          <div style={styles.tabRow}>
            {allJobs.map((j, idx) => {
              const lang = j.language || j.target_language || `Language ${idx + 1}`;
              return (
                <button
                  key={idx}
                  onClick={() => setActiveTab(idx)}
                  style={{
                    ...styles.tab,
                    ...(activeTab === idx ? styles.tabActive : {}),
                  }}
                >
                  {lang}
                </button>
              );
            })}
          </div>
        )}

        {/* Video Player */}
        <div style={styles.playerWrapper}>
          {videoUrl ? (
            <video
              key={videoUrl}
              style={styles.video}
              controls
              autoPlay={false}
              preload="metadata"
            >
              <source src={videoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          ) : (
            <div style={styles.noVideo}>
              <Play size={48} style={{ color: 'var(--text-secondary)', marginBottom: 16 }} />
              <p style={styles.noVideoText}>Video not yet available.</p>
            </div>
          )}
        </div>

        {/* Info */}
        <div style={styles.infoRow}>
          <div>
            <h2 style={styles.langTitle}>{language}</h2>
            <p style={styles.langSub}>Translated video</p>
          </div>
        </div>

        {/* Actions */}
        <div style={styles.actionsRow}>
          <button onClick={handleCopy} style={styles.actionBtn}>
            {copied ? (
              <><Check size={16} style={{ marginRight: 8 }} />Copied!</>
            ) : (
              <><Copy size={16} style={{ marginRight: 8 }} />Copy Link</>
            )}
          </button>
          {videoUrl && (
            <button onClick={handleDownload} style={styles.actionBtn}>
              <Download size={16} style={{ marginRight: 8 }} />
              Download
            </button>
          )}
          <button onClick={() => navigate('/')} style={styles.translateBtn}>
            <ArrowLeft size={16} style={{ marginRight: 8 }} />
            Translate Another
          </button>
        </div>
      </motion.div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '40px 20px 80px',
  },
  loadingWrapper: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '50vh',
  },
  loadingOrb: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    background: 'var(--primary)',
    marginBottom: '20px',
  },
  loadingText: {
    fontSize: '1rem',
    color: 'var(--text-secondary)',
  },
  errorCard: {
    background: 'rgba(20, 20, 31, 0.6)',
    backdropFilter: 'blur(16px)',
    border: '1px solid rgba(255, 87, 87, 0.3)',
    borderRadius: 'var(--radius-lg)',
    padding: '40px 32px',
    textAlign: 'center',
  },
  errorText: {
    fontSize: '1rem',
    color: 'var(--error)',
    marginBottom: '24px',
  },
  tabRow: {
    display: 'flex',
    gap: '4px',
    padding: '4px',
    background: 'rgba(10, 10, 15, 0.8)',
    borderRadius: 'var(--radius-md)',
    marginBottom: '24px',
    overflowX: 'auto',
    flexWrap: 'wrap',
  },
  tab: {
    padding: '10px 20px',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--text-secondary)',
    borderRadius: 'var(--radius-sm)',
    transition: 'all var(--transition)',
    whiteSpace: 'nowrap',
    cursor: 'pointer',
  },
  tabActive: {
    background: 'var(--surface)',
    color: 'var(--text)',
    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
  },
  playerWrapper: {
    width: '100%',
    borderRadius: 'var(--radius-lg)',
    overflow: 'hidden',
    background: '#000',
    border: '1px solid var(--border)',
    aspectRatio: '16 / 9',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  video: {
    width: '100%',
    height: '100%',
    display: 'block',
    objectFit: 'contain',
    background: '#000',
  },
  noVideo: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
  noVideoText: {
    fontSize: '0.95rem',
    color: 'var(--text-secondary)',
  },
  infoRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: '24px',
    marginBottom: '20px',
  },
  langTitle: {
    fontSize: '1.4rem',
    fontWeight: 800,
    color: 'var(--text)',
    letterSpacing: '-0.02em',
  },
  langSub: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    marginTop: '2px',
  },
  actionsRow: {
    display: 'flex',
    gap: '10px',
    flexWrap: 'wrap',
  },
  actionBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '12px 20px',
    fontSize: '0.875rem',
    fontWeight: 600,
    color: 'var(--text)',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    cursor: 'pointer',
    transition: 'all var(--transition)',
  },
  translateBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '12px 20px',
    fontSize: '0.875rem',
    fontWeight: 600,
    color: '#fff',
    background: 'linear-gradient(135deg, var(--primary), #6246E5)',
    borderRadius: 'var(--radius-sm)',
    cursor: 'pointer',
    transition: 'all var(--transition)',
    marginLeft: 'auto',
  },
  primaryBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '12px 24px',
    fontSize: '0.9rem',
    fontWeight: 600,
    color: '#fff',
    background: 'linear-gradient(135deg, var(--primary), #6246E5)',
    borderRadius: 'var(--radius-sm)',
    cursor: 'pointer',
    transition: 'all var(--transition)',
  },
};
