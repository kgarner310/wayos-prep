import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { Artifact, WorkersCompSnapshotArtifact } from '../services/types';
import ArtifactCard from './ArtifactCard';

interface WorkersCompCardProps {
  artifact: Artifact;
  content: WorkersCompSnapshotArtifact;
}

function modColor(mod: number | null, industryAvg: number | null): string {
  if (mod == null) return colors.textSecondary;
  if (industryAvg != null) {
    if (mod <= industryAvg * 0.9) return colors.success;
    if (mod >= industryAvg * 1.1) return colors.danger;
  }
  if (mod <= 1.0) return colors.success;
  if (mod <= 1.2) return colors.warning;
  return colors.danger;
}

function signalColor(signal: string): string {
  const s = signal?.toLowerCase() || '';
  if (s.includes('favorable') || s.includes('good') || s.includes('low'))
    return colors.success;
  if (s.includes('unfavorable') || s.includes('high') || s.includes('concern'))
    return colors.danger;
  return colors.warning;
}

export default function WorkersCompCard({
  artifact,
  content,
}: WorkersCompCardProps) {
  const mc = modColor(content.mod, content.industry_average_mod);

  return (
    <ArtifactCard
      artifactType={artifact.artifact_type}
      title={artifact.title}
      status={artifact.status}
      confidence={artifact.confidence}
    >
      {/* Mod Display */}
      <View style={styles.modRow}>
        <View style={styles.modBlock}>
          <Text style={styles.modLabel}>Mod Rate</Text>
          <Text style={[styles.modValue, { color: mc }]}>
            {content.mod != null ? content.mod.toFixed(2) : '--'}
          </Text>
        </View>
        <View style={styles.modBlock}>
          <Text style={styles.modLabel}>Industry Avg</Text>
          <Text style={styles.modAvg}>
            {content.industry_average_mod != null
              ? content.industry_average_mod.toFixed(2)
              : '--'}
          </Text>
        </View>
      </View>

      {/* Premium Signal */}
      {content.premium_signal ? (
        <View
          style={[
            styles.signalBadge,
            { backgroundColor: signalColor(content.premium_signal) + '18' },
          ]}
        >
          <Text
            style={[
              styles.signalText,
              { color: signalColor(content.premium_signal) },
            ]}
          >
            {content.premium_signal}
          </Text>
        </View>
      ) : null}

      {/* Risk Drivers */}
      {content.risk_drivers?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Risk Drivers</Text>
          {content.risk_drivers.map((driver, i) => (
            <View key={i} style={styles.bulletRow}>
              <View style={[styles.dot, { backgroundColor: colors.danger }]} />
              <Text style={styles.bulletText}>{driver}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Improvement Opportunities */}
      {content.improvement_opportunities?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Improvement Opportunities</Text>
          {content.improvement_opportunities.map((opp, i) => (
            <View key={i} style={styles.bulletRow}>
              <View style={[styles.dot, { backgroundColor: colors.success }]} />
              <Text style={styles.bulletText}>{opp}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Unknowns */}
      {content.unknowns?.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, styles.dimmed]}>Unknowns</Text>
          {content.unknowns.map((unknown, i) => (
            <View key={i} style={styles.bulletRow}>
              <Text style={[styles.unknownIcon, styles.dimmed]}>?</Text>
              <Text style={[styles.bulletText, styles.dimmed]}>{unknown}</Text>
            </View>
          ))}
        </View>
      )}
    </ArtifactCard>
  );
}

const styles = StyleSheet.create({
  modRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  modBlock: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: spacing.sm,
    alignItems: 'center',
  },
  modLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
    marginBottom: 2,
  },
  modValue: {
    fontSize: 28,
    fontWeight: '800',
  },
  modAvg: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.textSecondary,
  },
  signalBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: spacing.md,
  },
  signalText: {
    fontSize: 13,
    fontWeight: '600',
  },
  section: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
    marginRight: spacing.sm,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  unknownIcon: {
    fontSize: 14,
    fontWeight: '600',
    marginRight: spacing.sm,
    lineHeight: 20,
    color: colors.textSecondary,
  },
  dimmed: {
    opacity: 0.5,
  },
});
