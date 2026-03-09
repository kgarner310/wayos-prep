import React, { useCallback, useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { ArtifactStatus } from '../services/types';
import StatusBadge from './StatusBadge';

interface ArtifactCardProps {
  artifactType: string;
  title: string;
  status: ArtifactStatus;
  confidence?: number | null;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

const TYPE_COLORS: Record<string, string> = {
  coverage_gap: colors.danger,
  meeting_brief: colors.primary,
  workers_comp_snapshot: colors.warning,
  winnability: colors.success,
};

const TYPE_LABELS: Record<string, string> = {
  coverage_gap: 'Coverage Gap',
  meeting_brief: 'Meeting Brief',
  workers_comp_snapshot: 'Workers Comp',
  winnability: 'Winnability',
};

export default function ArtifactCard({
  artifactType,
  title,
  status,
  confidence,
  children,
  defaultExpanded = true,
}: ArtifactCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const borderColor = TYPE_COLORS[artifactType] || colors.border;
  const typeLabel = TYPE_LABELS[artifactType] || artifactType;

  const toggle = useCallback(() => setExpanded((prev) => !prev), []);

  return (
    <View style={[styles.card, { borderLeftColor: borderColor }]}>
      <Pressable style={styles.header} onPress={toggle}>
        <View style={styles.headerLeft}>
          <Text style={styles.typeLabel}>{typeLabel}</Text>
          <Text style={styles.title} numberOfLines={expanded ? undefined : 1}>
            {title}
          </Text>
        </View>
        <View style={styles.headerRight}>
          <StatusBadge status={status} confidence={confidence} />
          <Text style={styles.chevron}>{expanded ? '\u25B2' : '\u25BC'}</Text>
        </View>
      </Pressable>

      {expanded && <View style={styles.body}>{children}</View>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderLeftWidth: 4,
    marginBottom: spacing.md,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
  },
  headerLeft: {
    flex: 1,
    marginRight: spacing.sm,
  },
  typeLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  chevron: {
    fontSize: 10,
    color: colors.textSecondary,
  },
  body: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.md,
  },
});
