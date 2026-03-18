import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

const LANGUAGES = [
  { code: 'es', name: 'Spanish', native: 'Espanol' },
  { code: 'pt', name: 'Portuguese', native: 'Portugues' },
  { code: 'fr', name: 'French', native: 'Francais' },
  { code: 'de', name: 'German', native: 'Deutsch' },
  { code: 'zh', name: 'Mandarin', native: 'Zhongwen' },
  { code: 'ja', name: 'Japanese', native: 'Nihongo' },
  { code: 'th', name: 'Thai', native: 'Phasathai' },
  { code: 'hi', name: 'Hindi', native: 'Hindi' },
  { code: 'ar', name: 'Arabic', native: 'Arabiyya' },
  { code: 'yo', name: 'Yoruba', native: 'Yoruba' },
  { code: 'ig', name: 'Igbo', native: 'Igbo' },
  { code: 'sw', name: 'Swahili', native: 'Kiswahili' },
  { code: 'ko', name: 'Korean', native: 'Hangugeo' },
];

const styles = {
  wrapper: {
    width: '100%',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
  },
  label: {
    fontSize: '0.95rem',
    fontWeight: 600,
    color: 'var(--text)',
  },
  selectAll: {
    fontSize: '0.85rem',
    fontWeight: 500,
    color: 'var(--primary)',
    cursor: 'pointer',
    padding: '6px 14px',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--primary)',
    transition: 'all 200ms ease',
    background: 'transparent',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '10px',
  },
  pill: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    borderRadius: 'var(--radius-md)',
    cursor: 'pointer',
    border: '1px solid var(--border)',
    transition: 'all 200ms ease',
    overflow: 'hidden',
    userSelect: 'none',
  },
  pillSelected: {
    background: 'var(--primary)',
    borderColor: 'var(--primary)',
    color: '#fff',
  },
  pillUnselected: {
    background: 'transparent',
    borderColor: 'var(--border)',
    color: 'var(--text-secondary)',
  },
  langInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  langName: {
    fontSize: '0.875rem',
    fontWeight: 600,
    lineHeight: 1.2,
  },
  langCode: {
    fontSize: '0.7rem',
    fontWeight: 500,
    fontFamily: 'var(--font-mono)',
    opacity: 0.7,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  checkIcon: {
    flexShrink: 0,
    width: '18px',
    height: '18px',
  },
};

const mediaQuery = `
  @media (max-width: 768px) {
    .lang-grid { grid-template-columns: repeat(2, 1fr) !important; }
  }
  @media (min-width: 769px) and (max-width: 1024px) {
    .lang-grid { grid-template-columns: repeat(3, 1fr) !important; }
  }
`;

export default function LanguagePicker({ selected, onSelect }) {
  const allSelected = selected.length === LANGUAGES.length;

  const toggleAll = () => {
    if (allSelected) {
      onSelect([]);
    } else {
      onSelect(LANGUAGES.map((l) => l.code));
    }
  };

  const toggleLang = (code) => {
    if (selected.includes(code)) {
      onSelect(selected.filter((c) => c !== code));
    } else {
      onSelect([...selected, code]);
    }
  };

  return (
    <div style={styles.wrapper}>
      <style>{mediaQuery}</style>
      <div style={styles.header}>
        <span style={styles.label}>Target Languages</span>
        <button
          onClick={toggleAll}
          style={{
            ...styles.selectAll,
            ...(allSelected
              ? { background: 'var(--primary)', color: '#fff', borderColor: 'var(--primary)' }
              : {}),
          }}
        >
          {allSelected ? 'Deselect All' : 'Select All'}
        </button>
      </div>
      <div className="lang-grid" style={styles.grid}>
        {LANGUAGES.map((lang) => {
          const isSelected = selected.includes(lang.code);
          return (
            <motion.button
              key={lang.code}
              onClick={() => toggleLang(lang.code)}
              style={{
                ...styles.pill,
                ...(isSelected ? styles.pillSelected : styles.pillUnselected),
              }}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              layout
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            >
              <div style={styles.langInfo}>
                <span style={styles.langName}>{lang.name}</span>
                <span style={styles.langCode}>{lang.code}</span>
              </div>
              {isSelected && (
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                >
                  <Check size={18} style={styles.checkIcon} />
                </motion.div>
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

export { LANGUAGES };
