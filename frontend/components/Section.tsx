import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing } from '../services/theme';

interface SectionProps {
  title: string;
  items?: string[];
  text?: string;
}

export function Section({ title, items, text }: SectionProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      {text && <Text style={styles.text}>{text}</Text>}
      {items?.map((item, i) => (
        <View key={i} style={styles.bulletRow}>
          <Text style={styles.bullet}>•</Text>
          <Text style={styles.bulletText}>{item}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing.sm,
  },
  text: {
    fontSize: 15,
    color: colors.text,
    lineHeight: 22,
  },
  bulletRow: {
    flexDirection: 'row',
    paddingRight: spacing.md,
    marginBottom: 6,
  },
  bullet: {
    fontSize: 15,
    color: colors.accent,
    marginRight: spacing.sm,
    lineHeight: 22,
  },
  bulletText: {
    flex: 1,
    fontSize: 15,
    color: colors.text,
    lineHeight: 22,
  },
});
