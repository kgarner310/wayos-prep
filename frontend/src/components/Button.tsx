import React from 'react';
import { colors } from '../services/theme';

interface ButtonProps {
  title: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'accent';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  small?: boolean;
}

export function Button({
  title,
  onClick,
  variant = 'primary',
  disabled = false,
  loading = false,
  fullWidth = true,
  small = false,
}: ButtonProps) {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: small ? '8px 14px' : '12px 20px',
    borderRadius: 10,
    fontWeight: 600,
    fontSize: small ? 13 : 15,
    border: 'none',
    width: fullWidth ? '100%' : 'auto',
    opacity: disabled || loading ? 0.6 : 1,
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all 0.15s ease',
    letterSpacing: 0.2,
  };

  const variants: Record<string, React.CSSProperties> = {
    primary: { background: colors.primary, color: colors.white },
    secondary: { background: colors.background, color: colors.primary, border: `1.5px solid ${colors.border}` },
    outline: { background: 'transparent', color: colors.primary, border: `1.5px solid ${colors.primary}` },
    accent: { background: colors.accent, color: colors.white },
  };

  return (
    <button
      style={{ ...baseStyle, ...variants[variant] }}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? 'Working...' : title}
    </button>
  );
}
