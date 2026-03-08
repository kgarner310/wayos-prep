import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';

interface LoadingCardProps {
  label?: string;
}

export default function LoadingCard({ label }: LoadingCardProps) {
  const opacity = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.4,
          duration: 800,
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, [opacity]);

  return (
    <View style={styles.card}>
      <Animated.View style={[styles.shimmerLine, styles.lineShort, { opacity }]} />
      <Animated.View style={[styles.shimmerLine, styles.lineLong, { opacity }]} />
      <Animated.View style={[styles.shimmerLine, styles.lineMedium, { opacity }]} />
      {label && <Text style={styles.label}>{label}</Text>}
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
  shimmerLine: {
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.border,
    marginBottom: spacing.sm,
  },
  lineShort: {
    width: '40%',
  },
  lineLong: {
    width: '90%',
  },
  lineMedium: {
    width: '65%',
  },
  label: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    fontWeight: '500',
  },
});
