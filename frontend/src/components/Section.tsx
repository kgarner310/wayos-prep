import React from 'react';
import { colors } from '../services/theme';

interface SectionProps {
  title: string;
  items?: string[];
  text?: string;
}

export function Section({ title, items, text }: SectionProps) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: colors.primary,
          textTransform: 'uppercase',
          letterSpacing: 0.8,
          marginBottom: 6,
        }}
      >
        {title}
      </div>
      {text && (
        <div style={{ fontSize: 13, color: colors.text, lineHeight: 1.5 }}>
          {text}
        </div>
      )}
      {items?.map((item, i) => (
        <div
          key={i}
          style={{ display: 'flex', gap: 6, marginBottom: 4, paddingRight: 4 }}
        >
          <span style={{ color: colors.accent, fontSize: 13, lineHeight: 1.5 }}>
            •
          </span>
          <span style={{ fontSize: 13, color: colors.text, lineHeight: 1.5 }}>
            {item}
          </span>
        </div>
      ))}
    </div>
  );
}
