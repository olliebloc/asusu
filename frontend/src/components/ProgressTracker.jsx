import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, Copy, ExternalLink, RefreshCw } from 'lucide-react';
import { getJobStatus } from '../api';

const STEP_LABELS = [
  'Downloading video...',
  'Separating audio...',
  'Transcribing...',
  'Translating...',
  'Generating speech...',
  'Mixing audio...',
  'Uploading...',
];

function stepToIndex(step) {
  if (!step) return 0;
  const s = step.toLowerCase();
  if (s.includes('download')) return 0;
  if (s.includes('separat') || s.includes('extract')) return 1;
  if (s.includes('transcrib')) return 2;
  if (s.includes('translat')) return 3;
  if (s.includes('generat') || s.includes('speech') || s.includes('synth') || s.includes('tts')) return 4;
  if (s.includes('mix') || s.includes('merge') || s.includes('combin')) return 5;
  if (s.includes('upload') || s.includes('publish')) return 6;
  return 0;
}

export default function ProgressTracker() {
  const { jobIds: jobIdsParam } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState({});
  const [copied, setCopied] = useState(null);
  const intervalsRef = useRef({});

  const jobIds = jobIdsParam ? jobIdsParam.split(',').filter(Boolean) : [];

  // Initialize from navigation state if available
  useEffect(() => {
    if (location.state?.jobs) {
      const initial = {};
      location.state.jobs.forEach((j) => {
        const id = j.job_id || j.id;
        initial[id] = {
          id,
          language: j.language || j.target_language || 'Unknown',
          status: j.status || 'pending',
          progress: j.progress || 0,
          step: j.step || j.current_step || STEP_LABELS[0],
          result_url: j.result_url || null,
          error: j.error || null,
        };
      });
      setJobs(initial);
    }
  }, []);

  const pollJob = useCallback(async (jobId) => {
    try {
      const data = await getJobStatus(jobId);
      // Backend returns: {job_id, state, progress, step, total_steps, message, result, error}
      const state = (data.state || '').toUpperCase();
      const isSuccess = state === 'SUCCESS';
      const isFailure = state === 'FAILURE';
      const status = isSuccess ? 'completed' : isFailure ? 'failed' : 'processing';

      setJobs((prev) => ({
        ...prev,
        [jobId]: {
          id: jobId,
          language: prev[jobId]?.language || 'Unknown',
          status,
          progress: data.progress ?? prev[jobId]?.progress ?? 0,
          step: data.message || prev[jobId]?.step || STEP_LABELS[0],
          stepNum: data.step || null,
          totalSteps: data.total_steps || 7,
          result_url: data.result?.url || null,
          result: data.result || null,
          error: data.error || null,
        },
      }));

      // Stop polling if complete or failed
      if (isSuccess || isFailure) {
        if (intervalsRef.current[jobId]) {
          clearInterval(intervalsRef.current[jobId]);
          delete intervalsRef.current[jobId];
        }
      }
    } catch {
      // Keep polling on network errors
    }
  }, []);

  useEffect(() => {
    jobIds.forEach((jobId) => {
      // Initial fetch
      pollJob(jobId);
      // Poll every 2 seconds
      intervalsRef.current[jobId] = setInterval(() => pollJob(jobId), 2000);
    });

    return () => {
      Object.values(intervalsRef.current).forEach(clearInterval);
      intervalsRef.current = {};
    };
  }, [jobIdsParam]);

  const handleCopyLink = (url, jobId) => {
    navigator.clipboard.writeText(url).then(() => {
      setCopied(jobId);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  const isComplete = (status) => status === 'completed' || status === 'complete';
  const isFailed = (status) => status === 'failed';

  return (
    <div style={styles.container}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 style={styles.title}>Translation Progress</h1>
        <p style={styles.subtitle}>
          {jobIds.length} language{jobIds.length !== 1 ? 's' : ''} in progress
        </p>
      </motion.div>

      <div style={styles.jobList}>
        <AnimatePresence>
          {jobIds.map((jobId, idx) => {
            const job = jobs[jobId] || {
              id: jobId,
              language: 'Loading...',
              status: 'pending',
              progress: 0,
              step: STEP_LABELS[0],
            };
            const stepNum = job.stepNum || stepToIndex(job.step) + 1;
            const complete = isComplete(job.status);
            const failed = isFailed(job.status);
            const progress = complete ? 100 : job.progress;

            return (
              <motion.div
                key={jobId}
                style={{
                  ...styles.jobCard,
                  ...(complete ? styles.jobComplete : {}),
                  ...(failed ? styles.jobFailed : {}),
                }}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.05 }}
              >
                <div style={styles.jobHeader}>
                  <div style={styles.langLabel}>
                    {complete && <CheckCircle size={18} style={{ color: 'var(--success)', marginRight: 8 }} />}
                    {failed && <XCircle size={18} style={{ color: 'var(--error)', marginRight: 8 }} />}
                    <span style={styles.langName}>{job.language}</span>
                  </div>
                  <span style={styles.stepLabel}>
                    {complete ? 'Complete' : failed ? 'Failed' : `Step ${stepNum} of 7`}
                  </span>
                </div>

                {/* Progress bar */}
                <div style={styles.progressTrack}>
                  <motion.div
                    style={{
                      ...styles.progressBar,
                      ...(complete ? styles.progressComplete : {}),
                      ...(failed ? styles.progressFailed : {}),
                    }}
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                  />
                </div>

                <div style={styles.jobFooter}>
                  <span style={styles.stepText}>
                    {complete
                      ? 'Translation finished!'
                      : failed
                      ? job.error || 'An error occurred.'
                      : job.step || STEP_LABELS[stepNum - 1]}
                  </span>
                  <span style={styles.percent}>{Math.round(progress)}%</span>
                </div>

                {/* Actions */}
                {complete && job.result_url && (
                  <motion.div
                    style={styles.actions}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    transition={{ duration: 0.3 }}
                  >
                    <Link
                      to={`/v/${jobId}`}
                      style={styles.viewBtn}
                    >
                      <ExternalLink size={14} style={{ marginRight: 6 }} />
                      View Translated Video
                    </Link>
                    <button
                      onClick={() => handleCopyLink(job.result_url, jobId)}
                      style={styles.copyBtn}
                    >
                      <Copy size={14} style={{ marginRight: 6 }} />
                      {copied === jobId ? 'Copied!' : 'Copy Link'}
                    </button>
                  </motion.div>
                )}

                {failed && (
                  <motion.div
                    style={styles.actions}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                  >
                    <button
                      onClick={() => {
                        // Re-start polling
                        pollJob(jobId);
                        intervalsRef.current[jobId] = setInterval(() => pollJob(jobId), 2000);
                      }}
                      style={styles.retryBtn}
                    >
                      <RefreshCw size={14} style={{ marginRight: 6 }} />
                      Retry
                    </button>
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      <motion.div
        style={styles.backRow}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <button onClick={() => navigate('/')} style={styles.backBtn}>
          Translate Another Video
        </button>
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
  title: {
    fontSize: 'clamp(1.5rem, 3vw, 2rem)',
    fontWeight: 800,
    color: 'var(--text)',
    letterSpacing: '-0.02em',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '1rem',
    color: 'var(--text-secondary)',
    marginBottom: '32px',
  },
  jobList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  jobCard: {
    background: 'rgba(20, 20, 31, 0.6)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: '20px 24px',
    transition: 'border-color 300ms ease',
  },
  jobComplete: {
    borderColor: 'rgba(0, 212, 170, 0.3)',
  },
  jobFailed: {
    borderColor: 'rgba(255, 87, 87, 0.3)',
  },
  jobHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '12px',
  },
  langLabel: {
    display: 'flex',
    alignItems: 'center',
  },
  langName: {
    fontSize: '1rem',
    fontWeight: 700,
    color: 'var(--text)',
  },
  stepLabel: {
    fontSize: '0.8rem',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-secondary)',
    letterSpacing: '0.03em',
  },
  progressTrack: {
    width: '100%',
    height: '6px',
    background: 'var(--bg)',
    borderRadius: '3px',
    overflow: 'hidden',
    marginBottom: '10px',
  },
  progressBar: {
    height: '100%',
    borderRadius: '3px',
    background: 'linear-gradient(90deg, var(--primary), #9580FF)',
    boxShadow: '0 0 12px var(--primary-glow)',
    transition: 'background 300ms ease',
  },
  progressComplete: {
    background: 'linear-gradient(90deg, var(--secondary), #00E6B8)',
    boxShadow: '0 0 12px var(--secondary-glow)',
  },
  progressFailed: {
    background: 'var(--error)',
    boxShadow: '0 0 12px rgba(255, 87, 87, 0.25)',
  },
  jobFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stepText: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  percent: {
    fontSize: '0.85rem',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text)',
  },
  actions: {
    display: 'flex',
    gap: '10px',
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid var(--border)',
    overflow: 'hidden',
    flexWrap: 'wrap',
  },
  viewBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '10px 18px',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#fff',
    background: 'linear-gradient(135deg, var(--primary), #6246E5)',
    borderRadius: 'var(--radius-sm)',
    textDecoration: 'none',
    transition: 'all var(--transition)',
  },
  copyBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '10px 18px',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--text)',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    transition: 'all var(--transition)',
    cursor: 'pointer',
  },
  retryBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '10px 18px',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#fff',
    background: 'var(--error)',
    borderRadius: 'var(--radius-sm)',
    cursor: 'pointer',
    transition: 'all var(--transition)',
  },
  backRow: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: '40px',
  },
  backBtn: {
    padding: '12px 28px',
    fontSize: '0.9rem',
    fontWeight: 600,
    color: 'var(--text-secondary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    transition: 'all var(--transition)',
    cursor: 'pointer',
  },
};
