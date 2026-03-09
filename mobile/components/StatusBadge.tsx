import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { ArtifactStatus } from '../services/types';

interface StatusBadgeProps {
  status: ArtifactStatus;
  confidence?: number | null;
}

const STATUS_CONFIG: Record<
  ArtifactStatus,
  { label: string; color: string; bg: string }
> = {
  pending: {
    label: 'Pending',
    color: colors.warning,
    bg: '#FEF3C7',
  },
  ready: {
    label: 'Ready',
    color: colors.success,
    bg: '#ECFDF5',
  },
  failed: {
    label: 'Failed',
    color: colors.danger,
    bg: '#FEF2F2',
  },
};

function confidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return 'High';
  if (confidence >= 0.5) return 'Med';
  return 'Low';
}

export default function StatusBadge({ status, confidence }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;

  return (
    <View style={styles.row}>
      <View style={[styles.badge, { backgroundColor: config.bg }]}>
        <View style={[styles.dot, { backgroundColor: config.color }]} />
        <Text style={[styles.text, { color: config.color }]}>
          {config.label}
        </Text>
      </View>
      {confidence != null && status === 'ready' && (
        <View style={styles.confidenceBadge}>
          <Text style={styles.confidenceText}>
            {confidenceLabel(confidence)}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 4,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  text: {
    fontSize: 11,
    fontWeight: '600',
  },
  confidenceBadge: {
    backgroundColor: colors.background,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  confidenceText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.textSecondary,
  },
});
