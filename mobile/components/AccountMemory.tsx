import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { MemoryEntry } from '../services/types';

const TYPE_LABELS: Record<string, string> = {
  account_created: 'Created',
  brief_generated: 'Brief',
  brief_viewed: 'Viewed',
  producer_edited: 'Edited',
  producer_feedback: 'Feedback',
  outcome_logged: 'Outcome',
  renewal_started: 'Renewal',
  submission_packet_generated: 'Packet',
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

interface AccountMemoryProps {
  memory: MemoryEntry[];
}

export default function AccountMemory({ memory }: AccountMemoryProps) {
  if (!memory || memory.length === 0) return null;

  // Show most recent 5
  const recent = memory.slice(0, 5);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Account Memory</Text>
      {recent.map((entry) => (
        <View key={entry.id} style={styles.entry}>
          <View style={styles.entryHeader}>
            <View style={styles.typeBadge}>
              <Text style={styles.typeBadgeText}>
                {TYPE_LABELS[entry.entry_type] || entry.entry_type}
              </Text>
            </View>
            <Text style={styles.dateText}>{formatDate(entry.created_at)}</Text>
          </View>
          <Text style={styles.summary} numberOfLines={2}>
            {entry.summary}
          </Text>
        </View>
      ))}
      {memory.length > 5 && (
        <Text style={styles.moreText}>
          +{memory.length - 5} more entries
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: spacing.sm,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  entry: {
    backgroundColor: colors.surface,
    borderRadius: 10,
    padding: spacing.sm,
    marginBottom: spacing.xs,
    borderWidth: 1,
    borderColor: colors.border,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  typeBadge: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.primary,
  },
  dateText: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  summary: {
    fontSize: 13,
    color: colors.text,
    lineHeight: 18,
  },
  moreText: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
  },
});
