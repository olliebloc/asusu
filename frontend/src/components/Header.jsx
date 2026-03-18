import React from 'react';
import { Link } from 'react-router-dom';
import { Github } from 'lucide-react';

const styles = {
  header: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    height: '72px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 32px',
    background: 'rgba(10, 10, 15, 0.7)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderBottom: '1px solid var(--border)',
    zIndex: 100,
  },
  logo: {
    fontSize: '1.5rem',
    fontWeight: 800,
    color: 'var(--primary)',
    textDecoration: 'none',
    letterSpacing: '-0.02em',
  },
  tagline: {
    position: 'absolute',
    left: '50%',
    transform: 'translateX(-50%)',
    fontSize: '0.85rem',
    fontWeight: 400,
    color: 'var(--text-secondary)',
    letterSpacing: '0.04em',
    whiteSpace: 'nowrap',
  },
  githubLink: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '40px',
    height: '40px',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-secondary)',
    transition: 'color var(--transition), background var(--transition)',
  },
};

export default function Header() {
  return (
    <header style={styles.header}>
      <Link to="/" style={styles.logo}>
        Asụsụ
      </Link>
      <span style={styles.tagline}>Video, in every language</span>
      <a
        href="https://github.com"
        target="_blank"
        rel="noopener noreferrer"
        style={styles.githubLink}
        aria-label="GitHub"
        onMouseEnter={(e) => {
          e.currentTarget.style.color = 'var(--text)';
          e.currentTarget.style.background = 'var(--surface)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = 'var(--text-secondary)';
          e.currentTarget.style.background = 'none';
        }}
      >
        <Github size={20} />
      </a>
    </header>
  );
}
