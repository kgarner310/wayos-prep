import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { api } from '../services/api';
import { colors, spacing } from '../services/theme';

export default function AskScreen() {
  const router = useRouter();
  const [question, setQuestion] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!question.trim()) {
      Alert.alert('Required', 'Please enter a question about industry risks.');
      return;
    }

    setLoading(true);
    try {
      const brief = await api.askBrief(question.trim(), location.trim() || undefined);
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
          <Text style={styles.heading}>Ask a Risk Question</Text>
          <Text style={styles.hint}>
            Ask about any industry and we'll identify the risks and generate a
            meeting brief.
          </Text>

          <Input
            label="Your Question"
            placeholder='e.g., "What risks should I discuss with a roofing contractor?"'
            value={question}
            onChangeText={setQuestion}
            multiline
            numberOfLines={3}
            style={styles.multiline}
          />

          <Input
            label="Location"
            optional
            placeholder="e.g., North Carolina"
            value={location}
            onChangeText={setLocation}
          />

          <Button
            title="Generate Brief"
            onPress={handleGenerate}
            loading={loading}
            disabled={!question.trim()}
          />
        </Card>

        <View style={styles.examples}>
          <Text style={styles.examplesTitle}>Try asking:</Text>
          {[
            'What risks should I discuss with a roofing contractor?',
            'I have a meeting with a trucking company tomorrow.',
            'What exposures does a daycare center face?',
          ].map((ex, i) => (
            <Text
              key={i}
              style={styles.example}
              onPress={() => setQuestion(ex)}
            >
              "{ex}"
            </Text>
          ))}
        </View>
      </ScrollView>
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
  multiline: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  examples: {
    marginTop: spacing.lg,
  },
  examplesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  example: {
    fontSize: 14,
    color: colors.primaryLight,
    fontStyle: 'italic',
    marginBottom: spacing.sm,
    lineHeight: 20,
  },
});
