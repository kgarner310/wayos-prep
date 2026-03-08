import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  Pressable,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { colors } from '../../theme/colors';
import { spacing } from '../../theme/spacing';
import { submitOutcome } from '../../services/api';

const OUTCOMES = ['won', 'lost', 'renewed'] as const;
const REASONS = [
  'PRICE',
  'COVERAGE',
  'RELATIONSHIP',
  'APPETITE',
  'SERVICE',
  'UNKNOWN',
] as const;

type Outcome = (typeof OUTCOMES)[number];
type Reason = (typeof REASONS)[number];

export default function OutcomeScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [reason, setReason] = useState<Reason | null>(null);
  const [carrier, setCarrier] = useState('');
  const [premium, setPremium] = useState('');
  const [competitor, setCompetitor] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = useCallback(async () => {
    if (!outcome) {
      Alert.alert('Required', 'Please select an outcome.');
      return;
    }
    if (!reason) {
      Alert.alert('Required', 'Please select a reason.');
      return;
    }
    if (!id) return;

    try {
      setSubmitting(true);
      await submitOutcome({
        account_id: id,
        outcome,
        reason,
        carrier: carrier.trim() || undefined,
        premium: premium ? parseFloat(premium) : undefined,
        competitor: competitor.trim() || undefined,
        notes: notes.trim() || undefined,
      });

      Alert.alert('Success', 'Outcome logged successfully.', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to submit outcome.');
    } finally {
      setSubmitting(false);
    }
  }, [id, outcome, reason, carrier, premium, competitor, notes, router]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      {/* Outcome */}
      <View style={styles.field}>
        <Text style={styles.label}>Outcome *</Text>
        <View style={styles.optionRow}>
          {OUTCOMES.map((o) => (
            <Pressable
              key={o}
              style={[
                styles.optionButton,
                outcome === o && styles.optionButtonSelected,
                o === 'won' && outcome === o && styles.optionWon,
                o === 'lost' && outcome === o && styles.optionLost,
                o === 'renewed' && outcome === o && styles.optionRenewed,
              ]}
              onPress={() => setOutcome(o)}
            >
              <Text
                style={[
                  styles.optionText,
                  outcome === o && styles.optionTextSelected,
                ]}
              >
                {o.charAt(0).toUpperCase() + o.slice(1)}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Reason */}
      <View style={styles.field}>
        <Text style={styles.label}>Primary Reason *</Text>
        <View style={styles.reasonGrid}>
          {REASONS.map((r) => (
            <Pressable
              key={r}
              style={[
                styles.reasonChip,
                reason === r && styles.reasonChipSelected,
              ]}
              onPress={() => setReason(r)}
            >
              <Text
                style={[
                  styles.reasonText,
                  reason === r && styles.reasonTextSelected,
                ]}
              >
                {r}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Carrier */}
      <View style={styles.field}>
        <Text style={styles.label}>Carrier</Text>
        <TextInput
          style={styles.input}
          value={carrier}
          onChangeText={setCarrier}
          placeholder="e.g., Hartford"
          placeholderTextColor={colors.textSecondary}
        />
      </View>

      {/* Premium */}
      <View style={styles.field}>
        <Text style={styles.label}>Premium</Text>
        <TextInput
          style={styles.input}
          value={premium}
          onChangeText={setPremium}
          placeholder="e.g., 125000"
          placeholderTextColor={colors.textSecondary}
          keyboardType="number-pad"
        />
      </View>

      {/* Competitor */}
      <View style={styles.field}>
        <Text style={styles.label}>Competitor</Text>
        <TextInput
          style={styles.input}
          value={competitor}
          onChangeText={setCompetitor}
          placeholder="e.g., Marsh"
          placeholderTextColor={colors.textSecondary}
        />
      </View>

      {/* Notes */}
      <View style={styles.field}>
        <Text style={styles.label}>Notes</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          value={notes}
          onChangeText={setNotes}
          placeholder="Additional context..."
          placeholderTextColor={colors.textSecondary}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />
      </View>

      {/* Submit */}
      <Pressable
        style={[styles.submitButton, submitting && styles.submitDisabled]}
        onPress={handleSubmit}
        disabled={submitting}
      >
        {submitting ? (
          <ActivityIndicator color={colors.surface} size="small" />
        ) : (
          <Text style={styles.submitText}>Submit Outcome</Text>
        )}
      </Pressable>

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  field: {
    marginBottom: spacing.lg,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  optionRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  optionButton: {
    flex: 1,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  optionButtonSelected: {
    borderWidth: 2,
  },
  optionWon: {
    backgroundColor: '#ECFDF5',
    borderColor: colors.success,
  },
  optionLost: {
    backgroundColor: '#FEF2F2',
    borderColor: colors.danger,
  },
  optionRenewed: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  optionText: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  optionTextSelected: {
    color: colors.text,
  },
  reasonGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  reasonChip: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  reasonChipSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  reasonText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  reasonTextSelected: {
    color: colors.primary,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  textArea: {
    minHeight: 100,
  },
  submitButton: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  submitDisabled: {
    opacity: 0.6,
  },
  submitText: {
    color: colors.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  bottomSpacer: {
    height: spacing.xl,
  },
});
