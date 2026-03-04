import React from 'react';
import { colors } from '../services/theme';

interface CardProps {
  children: React.ReactNode;
  style?: React.CSSProperties;
  accentBorder?: boolean;
}

export function Card({ children, style, accentBorder }: CardProps) {
  return (
    <div
      style={{
        background: colors.surface,
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        borderLeft: accentBorder ? `4px solid ${colors.accent}` : undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
