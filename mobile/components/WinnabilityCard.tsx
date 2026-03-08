import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { Artifact, WinnabilityArtifact } from '../services/types';
import ArtifactCard from './ArtifactCard';

interface WinnabilityCardProps {
  artifact: Artifact;
  content: WinnabilityArtifact;
}

function bandColor(band: string): string {
  const b = band?.toLowerCase() || '';
  if (b === 'high' || b === 'strong') return colors.success;
  if (b === 'medium' || b === 'moderate') return colors.warning;
  if (b === 'low' || b === 'weak') return colors.danger;
  return colors.textSecondary;
}

export default function WinnabilityCard({
  artifact,
  content,
}: WinnabilityCardProps) {
  const bc = bandColor(content.band);

  return (
    <ArtifactCard
      artifactType={artifact.artifact_type}
      title={artifact.title}
      status={artifact.status}
      confidence={artifact.confidence}
    >
      {/* Score + Band */}
      <View style={styles.scoreRow}>
        <View style={styles.scoreBlock}>
          <Text style={[styles.scoreValue, { color: bc }]}>{content.score}</Text>
          <Text style={styles.scoreLabel}>/ 100</Text>
        </View>
        <View style={[styles.bandBadge, { backgroundColor: bc + '18' }]}>
          <Text style={[styles.bandText, { color: bc }]}>{content.band}</Text>
        </View>
      </View>

      {/* Score Bar */}
      <View style={styles.barContainer}>
        <View style={styles.barBackground}>
          <View
            style={[
              styles.barFill,
              {
                width: `${Math.min(100, Math.max(0, content.score))}%`,
                backgroundColor: bc,
              },
            ]}
          />
        </View>
      </View>

      {/* Reasons */}
      {content.reasons?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Factors</Text>
          {content.reasons.map((reason, i) => (
            <View key={i} style={styles.bulletRow}>
              <Text style={styles.bullet}>{'\u2022'}</Text>
              <Text style={styles.bulletText}>{reason}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Talking Points */}
      {content.talking_points?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Talking Points</Text>
          {content.talking_points.map((point, i) => (
            <View key={i} style={styles.talkingPointRow}>
              <Text style={styles.talkingPointIcon}>{'\u275D'}</Text>
              <Text style={styles.talkingPointText}>{point}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Next Actions */}
      {content.next_actions?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Next Actions</Text>
          {content.next_actions.map((action, i) => (
            <View key={i} style={styles.actionRow}>
              <View style={styles.actionCheckbox} />
              <Text style={styles.actionText}>{action}</Text>
            </View>
          ))}
        </View>
      )}
    </ArtifactCard>
  );
}

const styles = StyleSheet.create({
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
    gap: spacing.md,
  },
  scoreBlock: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  scoreValue: {
    fontSize: 36,
    fontWeight: '800',
  },
  scoreLabel: {
    fontSize: 16,
    color: colors.textSecondary,
    fontWeight: '500',
    marginLeft: 2,
  },
  bandBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
  },
  bandText: {
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  barContainer: {
    marginBottom: spacing.md,
  },
  barBackground: {
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: 6,
    borderRadius: 3,
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
  talkingPointRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.primaryLight,
    padding: spacing.sm,
    borderRadius: 6,
    marginBottom: 4,
  },
  talkingPointIcon: {
    fontSize: 12,
    color: colors.primary,
    marginRight: spacing.sm,
    marginTop: 2,
  },
  talkingPointText: {
    flex: 1,
    fontSize: 14,
    color: colors.primary,
    lineHeight: 20,
    fontWeight: '500',
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  actionCheckbox: {
    width: 16,
    height: 16,
    borderRadius: 4,
    borderWidth: 1.5,
    borderColor: colors.primary,
    marginRight: spacing.sm,
    marginTop: 2,
  },
  actionText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
});
