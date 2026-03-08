import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { InsightItem } from '../services/types';

interface InsightFeedItemProps {
  insight: InsightItem;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: colors.danger,
  high: colors.danger,
  medium: colors.warning,
  low: colors.info,
};

const TYPE_ICONS: Record<string, string> = {
  coverage: 'C',
  risk: 'R',
  compliance: '!',
  opportunity: 'O',
  workers_comp: 'W',
  carrier: 'K',
};

export default function InsightFeedItem({ insight }: InsightFeedItemProps) {
  const severityColor =
    SEVERITY_COLORS[insight.severity] || colors.textSecondary;
  const icon = TYPE_ICONS[insight.insight_type] || 'i';

  return (
    <View style={styles.container}>
      <View style={[styles.iconCircle, { backgroundColor: severityColor + '18' }]}>
        <Text style={[styles.iconText, { color: severityColor }]}>{icon}</Text>
      </View>
      <View style={styles.content}>
        <Text style={styles.title}>{insight.title}</Text>
        {insight.subtitle ? (
          <Text style={styles.subtitle}>{insight.subtitle}</Text>
        ) : null}
        {insight.suggested_action ? (
          <Text style={styles.action}>{insight.suggested_action}</Text>
        ) : null}
      </View>
      <View style={[styles.severityDot, { backgroundColor: severityColor }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderRadius: 10,
    padding: spacing.sm,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  iconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
    marginTop: 2,
  },
  iconText: {
    fontSize: 14,
    fontWeight: '700',
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    lineHeight: 19,
  },
  subtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
    marginTop: 2,
  },
  action: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: '500',
    lineHeight: 18,
    marginTop: 4,
  },
  severityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 6,
    marginLeft: spacing.sm,
  },
});
