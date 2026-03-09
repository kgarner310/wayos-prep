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
import { useRouter } from 'expo-router';
import { colors } from '../../theme/colors';
import { spacing } from '../../theme/spacing';
import { createManualAccount } from '../../services/api';

const COVERAGE_OPTIONS = [
  'General Liability',
  'Workers Compensation',
  'Commercial Auto',
  'Property',
  'Professional Liability',
  'Cyber',
  'Umbrella/Excess',
  'D&O',
  'EPLI',
  'Crime',
  'Inland Marine',
  'BOP',
];

export default function NewAccountScreen() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);

  const [accountName, setAccountName] = useState('');
  const [namedInsured, setNamedInsured] = useState('');
  const [industry, setIndustry] = useState('');
  const [state, setState] = useState('');
  const [employeeCount, setEmployeeCount] = useState('');
  const [workersCompMod, setWorkersCompMod] = useState('');
  const [currentCarriers, setCurrentCarriers] = useState('');
  const [selectedCoverages, setSelectedCoverages] = useState<Set<string>>(
    new Set()
  );

  const toggleCoverage = useCallback((coverage: string) => {
    setSelectedCoverages((prev) => {
      const next = new Set(prev);
      if (next.has(coverage)) {
        next.delete(coverage);
      } else {
        next.add(coverage);
      }
      return next;
    });
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!accountName.trim()) {
      Alert.alert('Required', 'Account name is required.');
      return;
    }
    if (!namedInsured.trim()) {
      Alert.alert('Required', 'Named insured is required.');
      return;
    }

    try {
      setSubmitting(true);

      const carriers = currentCarriers
        .split(',')
        .map((c) => c.trim())
        .filter(Boolean);

      const result = await createManualAccount({
        account_name: accountName.trim(),
        named_insured: namedInsured.trim(),
        industry: industry.trim(),
        state: state.trim().toUpperCase(),
        employee_count: employeeCount ? parseInt(employeeCount, 10) : null,
        workers_comp_mod: workersCompMod
          ? parseFloat(workersCompMod)
          : null,
        current_coverages: Array.from(selectedCoverages),
        current_carriers: carriers,
      });

      router.replace(`/account/${result.account.id}`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to create account.');
    } finally {
      setSubmitting(false);
    }
  }, [
    accountName,
    namedInsured,
    industry,
    state,
    employeeCount,
    workersCompMod,
    currentCarriers,
    selectedCoverages,
    router,
  ]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      {/* Account Name */}
      <View style={styles.field}>
        <Text style={styles.label}>Account Name *</Text>
        <TextInput
          style={styles.input}
          value={accountName}
          onChangeText={setAccountName}
          placeholder="e.g., Smith Manufacturing"
          placeholderTextColor={colors.textSecondary}
        />
      </View>

      {/* Named Insured */}
      <View style={styles.field}>
        <Text style={styles.label}>Named Insured *</Text>
        <TextInput
          style={styles.input}
          value={namedInsured}
          onChangeText={setNamedInsured}
          placeholder="e.g., Smith Manufacturing LLC"
          placeholderTextColor={colors.textSecondary}
        />
      </View>

      {/* Industry */}
      <View style={styles.field}>
        <Text style={styles.label}>Industry</Text>
        <TextInput
          style={styles.input}
          value={industry}
          onChangeText={setIndustry}
          placeholder="e.g., Manufacturing"
          placeholderTextColor={colors.textSecondary}
        />
      </View>

      {/* State */}
      <View style={styles.field}>
        <Text style={styles.label}>State</Text>
        <TextInput
          style={styles.input}
          value={state}
          onChangeText={setState}
          placeholder="e.g., CA"
          placeholderTextColor={colors.textSecondary}
          maxLength={2}
          autoCapitalize="characters"
        />
      </View>

      {/* Employee Count */}
      <View style={styles.field}>
        <Text style={styles.label}>Employee Count</Text>
        <TextInput
          style={styles.input}
          value={employeeCount}
          onChangeText={setEmployeeCount}
          placeholder="e.g., 150"
          placeholderTextColor={colors.textSecondary}
          keyboardType="number-pad"
        />
      </View>

      {/* Workers Comp Mod */}
      <View style={styles.field}>
        <Text style={styles.label}>Workers Comp Mod</Text>
        <TextInput
          style={styles.input}
          value={workersCompMod}
          onChangeText={setWorkersCompMod}
          placeholder="e.g., 1.05"
          placeholderTextColor={colors.textSecondary}
          keyboardType="decimal-pad"
        />
      </View>

      {/* Current Coverages */}
      <View style={styles.field}>
        <Text style={styles.label}>Current Coverages</Text>
        <View style={styles.coverageGrid}>
          {COVERAGE_OPTIONS.map((coverage) => {
            const selected = selectedCoverages.has(coverage);
            return (
              <Pressable
                key={coverage}
                style={[
                  styles.coverageChip,
                  selected && styles.coverageChipSelected,
                ]}
                onPress={() => toggleCoverage(coverage)}
              >
                <Text
                  style={[
                    styles.coverageChipText,
                    selected && styles.coverageChipTextSelected,
                  ]}
                >
                  {coverage}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Current Carriers */}
      <View style={styles.field}>
        <Text style={styles.label}>Current Carriers</Text>
        <TextInput
          style={styles.input}
          value={currentCarriers}
          onChangeText={setCurrentCarriers}
          placeholder="Comma-separated, e.g., Hartford, Travelers"
          placeholderTextColor={colors.textSecondary}
        />
      </View>

      {/* Submit */}
      <Pressable
        style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={submitting}
      >
        {submitting ? (
          <ActivityIndicator color={colors.surface} size="small" />
        ) : (
          <Text style={styles.submitButtonText}>Create Account</Text>
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
    marginBottom: spacing.md,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
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
  coverageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  coverageChip: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  coverageChipSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  coverageChipText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  coverageChipTextSelected: {
    color: colors.primary,
  },
  submitButton: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: spacing.md,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: colors.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  bottomSpacer: {
    height: spacing.xl,
  },
});
