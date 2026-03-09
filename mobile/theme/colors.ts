export const colors = {
  background: '#F8F9FA',
  surface: '#FFFFFF',
  primary: '#1A56DB',
  primaryLight: '#E1EFFE',
  text: '#1F2937',
  textSecondary: '#6B7280',
  border: '#E5E7EB',
  success: '#059669',
  warning: '#D97706',
  danger: '#DC2626',
  info: '#3B82F6',
} as const;

export type ColorName = keyof typeof colors;
