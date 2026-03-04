export const colors = {
  primary: '#1B2A4A',
  primaryLight: '#2C4270',
  accent: '#E8913A',
  accentLight: '#F0A85C',
  background: '#F5F6FA',
  surface: '#FFFFFF',
  text: '#1A1A2E',
  textSecondary: '#6B7280',
  textLight: '#9CA3AF',
  border: '#E5E7EB',
  success: '#10B981',
  error: '#EF4444',
  white: '#FFFFFF',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const typography = {
  h1: { fontSize: 28, fontWeight: '700' as const, color: colors.primary },
  h2: { fontSize: 22, fontWeight: '700' as const, color: colors.primary },
  h3: { fontSize: 18, fontWeight: '600' as const, color: colors.text },
  body: { fontSize: 16, color: colors.text },
  caption: { fontSize: 14, color: colors.textSecondary },
  small: { fontSize: 12, color: colors.textLight },
};
