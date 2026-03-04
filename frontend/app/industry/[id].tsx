import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { api, IndustryDetail } from '../../services/api';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Section } from '../../components/Section';
import { colors, spacing } from '../../services/theme';

export default function IndustryDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [industry, setIndustry] = useState<IndustryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (id) {
      api
        .getIndustry(parseInt(id, 10))
        .then(setIndustry)
        .catch((err) => Alert.alert('Error', err.message))
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleGenerateBrief = async () => {
    if (!industry) return;
    setGenerating(true);
    try {
      const brief = await api.prepBrief({
        industry: industry.industry_name,
        location: 'Not specified',
      });
      router.push(`/brief/${brief.id}`);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!industry) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Industry not found.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card style={styles.header}>
        <Text style={styles.title}>{industry.industry_name}</Text>
        {industry.synonyms.length > 0 && (
          <Text style={styles.synonyms}>
            Also: {industry.synonyms.join(', ')}
          </Text>
        )}
      </Card>

      <Card>
        <Section
          title="Workers' Comp Claims"
          items={industry.top_workers_comp_claims}
        />
        <Section
          title="Commercial Auto Claims"
          items={industry.commercial_auto_claims}
        />
        <Section
          title="General Liability Exposures"
          items={industry.general_liability_exposures}
        />
        <Section
          title="Conversation Prompts"
          items={industry.conversation_prompts}
        />
        {industry.regional_risk_notes && (
          <Section
            title="Regional Risk Notes"
            text={industry.regional_risk_notes}
          />
        )}
      </Card>

      <Button
        title="Generate Brief"
        onPress={handleGenerateBrief}
        loading={generating}
        style={styles.generateButton}
      />
    </ScrollView>
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
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.primary,
  },
  synonyms: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    fontStyle: 'italic',
  },
  errorText: {
    fontSize: 16,
    color: colors.error,
  },
  generateButton: {
    marginTop: spacing.md,
    marginBottom: spacing.xl,
  },
});
