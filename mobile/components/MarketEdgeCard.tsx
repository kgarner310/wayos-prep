import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { MarketEdge } from '../services/types';

interface MarketEdgeCardProps {
  marketEdge: MarketEdge;
}

export default function MarketEdgeCard({ marketEdge }: MarketEdgeCardProps) {
  if (marketEdge.confidence === 'low') {
    return (
      <View style={styles.card}>
        <Text style={styles.title}>MARKET EDGE</Text>
        <Text style={styles.sparse}>
          Insufficient WAYOS market data — more outcomes needed.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <Text style={styles.title}>MARKET EDGE</Text>
      <Text style={styles.subtitle}>
        {marketEdge.sample_size} outcomes in {marketEdge.industry} / {marketEdge.state}
      </Text>

      {/* Carrier Win Rates */}
      {marketEdge.carrier_win_rates.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Carrier Win Rates</Text>
          {marketEdge.carrier_win_rates.map((entry) => (
            <View key={entry.carrier} style={styles.barRow}>
              <Text style={styles.barLabel}>{entry.carrier}</Text>
              <View style={styles.barContainer}>
                <View
                  style={[
                    styles.barFill,
                    { width: `${Math.round(entry.win_rate * 100)}%` },
                  ]}
                />
              </View>
              <Text style={styles.barValue}>
                {Math.round(entry.win_rate * 100)}%
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Top Loss Reasons */}
      {marketEdge.top_loss_reasons.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Top Loss Reasons</Text>
          {marketEdge.top_loss_reasons.map((entry, i) => (
            <View key={entry.reason} style={styles.reasonRow}>
              <Text style={styles.reasonIndex}>{i + 1}.</Text>
              <Text style={styles.reasonText}>
                {entry.reason.replace(/_/g, ' ')}
              </Text>
              <Text style={styles.reasonCount}>{entry.count}</Text>
            </View>
          ))}
        </View>
      )}
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
  title: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.text,
    letterSpacing: 1,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  sparse: {
    fontSize: 14,
    color: colors.textSecondary,
    fontStyle: 'italic',
    marginTop: spacing.sm,
  },
  section: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  barRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  barLabel: {
    width: 100,
    fontSize: 13,
    color: colors.text,
    fontWeight: '500',
  },
  barContainer: {
    flex: 1,
    height: 8,
    backgroundColor: colors.border,
    borderRadius: 4,
    overflow: 'hidden',
    marginHorizontal: spacing.sm,
  },
  barFill: {
    height: 8,
    backgroundColor: colors.primary,
    borderRadius: 4,
  },
  barValue: {
    width: 36,
    fontSize: 13,
    fontWeight: '700',
    color: colors.text,
    textAlign: 'right',
  },
  reasonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  reasonIndex: {
    width: 20,
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  reasonText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    textTransform: 'capitalize',
  },
  reasonCount: {
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: '600',
  },
});
