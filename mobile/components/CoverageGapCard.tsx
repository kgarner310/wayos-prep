import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { Artifact, CoverageGapArtifact } from '../services/types';
import ArtifactCard from './ArtifactCard';

interface CoverageGapCardProps {
  artifact: Artifact;
  content: CoverageGapArtifact;
}

const RISK_COLORS: Record<string, string> = {
  high: colors.danger,
  critical: colors.danger,
  medium: colors.warning,
  low: colors.success,
};

export default function CoverageGapCard({
  artifact,
  content,
}: CoverageGapCardProps) {
  const riskColor = RISK_COLORS[content.risk_level?.toLowerCase()] || colors.warning;

  return (
    <ArtifactCard
      artifactType={artifact.artifact_type}
      title={artifact.title}
      status={artifact.status}
      confidence={artifact.confidence}
    >
      {/* Risk Level */}
      <View style={[styles.riskBadge, { backgroundColor: riskColor + '18' }]}>
        <Text style={[styles.riskText, { color: riskColor }]}>
          Risk: {content.risk_level}
        </Text>
      </View>

      {/* Gaps */}
      {content.gaps?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Coverage Gaps</Text>
          {content.gaps.map((gap, i) => (
            <View key={i} style={styles.bulletRow}>
              <Text style={styles.bullet}>{'\u2022'}</Text>
              <Text style={styles.bulletText}>{gap}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Duty to Advise */}
      {content.duty_to_advise_flags?.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.danger }]}>
            Duty to Advise
          </Text>
          {content.duty_to_advise_flags.map((flag, i) => (
            <View key={i} style={styles.flagRow}>
              <Text style={styles.flagIcon}>!</Text>
              <Text style={styles.flagText}>{flag}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Recommended Coverages */}
      {content.recommended_coverages?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recommended</Text>
          {content.recommended_coverages.map((cov, i) => (
            <View key={i} style={styles.bulletRow}>
              <Text style={[styles.bullet, { color: colors.success }]}>+</Text>
              <Text style={styles.bulletText}>{cov}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Talking Points */}
      {content.producer_talking_points?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Talking Points</Text>
          {content.producer_talking_points.map((point, i) => (
            <View key={i} style={styles.bulletRow}>
              <Text style={styles.bullet}>{'\u2022'}</Text>
              <Text style={styles.bulletText}>{point}</Text>
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
              <Text style={[styles.bullet, styles.dimmed]}>?</Text>
              <Text style={[styles.bulletText, styles.dimmed]}>{unknown}</Text>
            </View>
          ))}
        </View>
      )}
    </ArtifactCard>
  );
}

const styles = StyleSheet.create({
  riskBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: spacing.md,
  },
  riskText: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
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
  bullet: {
    fontSize: 14,
    color: colors.textSecondary,
    marginRight: spacing.sm,
    lineHeight: 20,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  flagRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF2F2',
    padding: spacing.sm,
    borderRadius: 6,
    marginBottom: 4,
  },
  flagIcon: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.danger,
    marginRight: spacing.sm,
    lineHeight: 20,
  },
  flagText: {
    flex: 1,
    fontSize: 14,
    color: colors.danger,
    lineHeight: 20,
    fontWeight: '500',
  },
  dimmed: {
    opacity: 0.5,
  },
});
