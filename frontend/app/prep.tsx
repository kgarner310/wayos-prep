import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  TouchableOpacity,
  FlatList,
  Modal,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { api, IndustryListItem } from '../services/api';
import { colors, spacing } from '../services/theme';

export default function PrepScreen() {
  const router = useRouter();
  const [industries, setIndustries] = useState<IndustryListItem[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [showPicker, setShowPicker] = useState(false);
  const [location, setLocation] = useState('');
  const [employeeCount, setEmployeeCount] = useState('');
  const [mod, setMod] = useState('');
  const [vehicleExposure, setVehicleExposure] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listIndustries().then(setIndustries).catch(() => {});
  }, []);

  const handleGenerate = async () => {
    if (!selectedIndustry) {
      Alert.alert('Required', 'Please select an industry.');
      return;
    }
    if (!location.trim()) {
      Alert.alert('Required', 'Please enter a location.');
      return;
    }

    setLoading(true);
    try {
      const brief = await api.prepBrief({
        industry: selectedIndustry,
        location: location.trim(),
        employee_count: employeeCount ? parseInt(employeeCount, 10) : undefined,
        mod: mod ? parseFloat(mod) : undefined,
        vehicle_exposure: vehicleExposure.trim() || undefined,
      });
      router.push(`/brief/${brief.id}`);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to generate brief.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Card>
          <Text style={styles.heading}>Prep This Account</Text>
          <Text style={styles.hint}>
            Enter account details to generate a tailored client brief.
          </Text>

          <Text style={styles.label}>Industry *</Text>
          <TouchableOpacity
            style={styles.picker}
            onPress={() => setShowPicker(true)}
          >
            <Text
              style={[
                styles.pickerText,
                !selectedIndustry && styles.placeholder,
              ]}
            >
              {selectedIndustry || 'Select an industry...'}
            </Text>
          </TouchableOpacity>

          <Input
            label="Location"
            placeholder="e.g., North Carolina"
            value={location}
            onChangeText={setLocation}
          />

          <Input
            label="Employee Count"
            optional
            placeholder="e.g., 12"
            value={employeeCount}
            onChangeText={setEmployeeCount}
            keyboardType="numeric"
          />

          <Input
            label="MOD (Experience Modifier)"
            optional
            placeholder="e.g., 1.15"
            value={mod}
            onChangeText={setMod}
            keyboardType="decimal-pad"
          />

          <Input
            label="Vehicle Exposure"
            optional
            placeholder="e.g., 5 trucks, 2 vans"
            value={vehicleExposure}
            onChangeText={setVehicleExposure}
          />

          <Button
            title="Generate Brief"
            onPress={handleGenerate}
            loading={loading}
            disabled={!selectedIndustry || !location.trim()}
          />
        </Card>
      </ScrollView>

      <Modal visible={showPicker} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Industry</Text>
              <TouchableOpacity onPress={() => setShowPicker(false)}>
                <Text style={styles.modalClose}>Done</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={industries}
              keyExtractor={(item) => item.id.toString()}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={[
                    styles.modalItem,
                    selectedIndustry === item.industry_name &&
                      styles.modalItemSelected,
                  ]}
                  onPress={() => {
                    setSelectedIndustry(item.industry_name);
                    setShowPicker(false);
                  }}
                >
                  <Text
                    style={[
                      styles.modalItemText,
                      selectedIndustry === item.industry_name &&
                        styles.modalItemTextSelected,
                    ]}
                  >
                    {item.industry_name}
                  </Text>
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
  },
  heading: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  hint: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
    lineHeight: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  picker: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: spacing.md,
    paddingVertical: 14,
    marginBottom: spacing.md,
  },
  pickerText: {
    fontSize: 16,
    color: colors.text,
  },
  placeholder: {
    color: colors.textLight,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '60%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.primary,
  },
  modalClose: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.accent,
  },
  modalItem: {
    paddingVertical: 14,
    paddingHorizontal: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalItemSelected: {
    backgroundColor: colors.background,
  },
  modalItemText: {
    fontSize: 16,
    color: colors.text,
  },
  modalItemTextSelected: {
    color: colors.accent,
    fontWeight: '600',
  },
});
