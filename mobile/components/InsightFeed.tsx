import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { InsightItem } from '../services/types';
import InsightFeedItem from './InsightFeedItem';

interface InsightFeedProps {
  insights: InsightItem[];
}

export default function InsightFeed({ insights }: InsightFeedProps) {
  if (!insights || insights.length === 0) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Insights</Text>
      {insights.map((insight, i) => (
        <InsightFeedItem key={i} insight={insight} />
      ))}
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
});
