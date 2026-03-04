import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from '../components/Button';
import { colors, spacing } from '../services/theme';

export default function HomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.hero}>
        <View style={styles.logoContainer}>
          <Text style={styles.logoText}>W</Text>
        </View>
        <Text style={styles.title}>WAYOS PREP</Text>
        <Text style={styles.subtitle}>
          Better meetings. Better coverage.
        </Text>
        <Text style={styles.description}>
          Generate professional client risk briefs in seconds.
          Walk into every meeting prepared.
        </Text>
      </View>

      <View style={styles.actions}>
        <Button
          title="Ask Risk Question"
          onPress={() => router.push('/ask')}
          variant="primary"
          style={styles.button}
        />
        <Button
          title="Prep This Account"
          onPress={() => router.push('/prep')}
          variant="secondary"
          style={styles.button}
        />
        <Button
          title="Industry Lookup"
          onPress={() => router.push('/lookup')}
          variant="outline"
          style={styles.button}
        />
      </View>

      <Text style={styles.footer}>wayosprep.app</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.lg,
  },
  hero: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: spacing.xl,
  },
  logoContainer: {
    width: 80,
    height: 80,
    borderRadius: 20,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  logoText: {
    fontSize: 40,
    fontWeight: '800',
    color: colors.accent,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: 16,
    color: colors.accent,
    fontWeight: '600',
    marginTop: spacing.xs,
    marginBottom: spacing.md,
  },
  description: {
    fontSize: 15,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: spacing.lg,
  },
  actions: {
    paddingBottom: spacing.xl,
  },
  button: {
    marginBottom: spacing.sm + 4,
  },
  footer: {
    textAlign: 'center',
    fontSize: 12,
    color: colors.textLight,
    paddingBottom: spacing.md,
  },
});
