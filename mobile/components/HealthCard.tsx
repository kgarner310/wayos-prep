import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { AccountHealth } from '../services/types';

interface HealthCardProps {
  health: AccountHealth;
}

function scoreColor(score: number): string {
  if (score >= 70) return colors.success;
  if (score >= 50) return colors.warning;
  if (score >= 30) return '#EA580C'; // orange
  return colors.danger;
}

function confidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return 'High';
  if (confidence >= 0.5) return 'Medium';
  return 'Low';
}

export default function HealthCard({ health }: HealthCardProps) {
  const color = scoreColor(health.overall_score);

  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        {/* Score Circle */}
        <View style={styles.scoreContainer}>
          <View style={[styles.scoreCircle, { borderColor: color }]}>
            <Text style={[styles.scoreValue, { color }]}>
              {health.overall_score}
            </Text>
            <Text style={styles.scoreLabel}>Score</Text>
          </View>
        </View>

        {/* Badges */}
        <View style={styles.badges}>
          <View style={styles.confidenceBadge}>
            <Text style={styles.confidenceText}>
              {confidenceLabel(health.confidence)} Confidence
            </Text>
          </View>
          {health.duty_to_advise_alert_count > 0 && (
            <View style={styles.dutyBadge}>
              <Text style={styles.dutyBadgeText}>
                {health.duty_to_advise_alert_count} Duty to Advise
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Score Breakdown */}
      <View style={styles.breakdown}>
        <ScoreItem
          label="Coverage"
          score={health.coverage_score}
        />
        <View style={styles.divider} />
        <ScoreItem
          label="Workers Comp"
          score={health.workers_comp_score}
        />
        <View style={styles.divider} />
        <ScoreItem
          label="Carrier Fit"
          score={health.carrier_fit_score}
        />
      </View>

      {/* Top Issues */}
      {health.top_issues.length > 0 && (
        <View style={styles.issuesContainer}>
          <Text style={styles.issuesTitle}>Top Issues</Text>
          {health.top_issues.map((issue, i) => (
            <View key={i} style={styles.issueRow}>
              <View style={styles.issueDot} />
              <Text style={styles.issueText}>{issue}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

function ScoreItem({ label, score }: { label: string; score: number }) {
  const color = scoreColor(score);
  return (
    <View style={styles.scoreItem}>
      <Text style={[styles.scoreItemValue, { color }]}>{score}</Text>
      <Text style={styles.scoreItemLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  scoreContainer: {
    marginRight: spacing.md,
  },
  scoreCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 4,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  scoreValue: {
    fontSize: 28,
    fontWeight: '800',
  },
  scoreLabel: {
    fontSize: 10,
    color: colors.textSecondary,
    fontWeight: '500',
    marginTop: -2,
  },
  badges: {
    flex: 1,
    gap: spacing.xs,
  },
  confidenceBadge: {
    backgroundColor: colors.primaryLight,
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
  },
  dutyBadge: {
    backgroundColor: '#FEF2F2',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  dutyBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.danger,
  },
  breakdown: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: spacing.sm,
  },
  scoreItem: {
    flex: 1,
    alignItems: 'center',
  },
  scoreItemValue: {
    fontSize: 20,
    fontWeight: '700',
  },
  scoreItemLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
    marginTop: 2,
  },
  divider: {
    width: 1,
    height: 28,
    backgroundColor: colors.border,
  },
  issuesContainer: {
    marginTop: spacing.md,
  },
  issuesTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  issueRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  issueDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: colors.warning,
    marginTop: 6,
    marginRight: spacing.sm,
  },
  issueText: {
    flex: 1,
    fontSize: 13,
    color: colors.text,
    lineHeight: 18,
  },
});
