import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { Artifact, MeetingBriefArtifact } from '../services/types';
import ArtifactCard from './ArtifactCard';

interface MeetingBriefCardProps {
  artifact: Artifact;
  content: MeetingBriefArtifact;
}

export default function MeetingBriefCard({
  artifact,
  content,
}: MeetingBriefCardProps) {
  return (
    <ArtifactCard
      artifactType={artifact.artifact_type}
      title={artifact.title}
      status={artifact.status}
      confidence={artifact.confidence}
    >
      {/* Client Summary */}
      {content.client_summary ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Client Summary</Text>
          <Text style={styles.summaryText}>{content.client_summary}</Text>
        </View>
      ) : null}

      {/* Key Risks */}
      {content.key_risks?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Risks</Text>
          {content.key_risks.map((risk, i) => (
            <View key={i} style={styles.bulletRow}>
              <View style={[styles.dot, { backgroundColor: colors.danger }]} />
              <Text style={styles.bulletText}>{risk}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Coverage Concerns */}
      {content.coverage_concerns?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Coverage Concerns</Text>
          {content.coverage_concerns.map((concern, i) => (
            <View key={i} style={styles.bulletRow}>
              <View style={[styles.dot, { backgroundColor: colors.warning }]} />
              <Text style={styles.bulletText}>{concern}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Questions for Client */}
      {content.questions_for_client?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Questions for Client</Text>
          {content.questions_for_client.map((question, i) => (
            <View key={i} style={styles.questionRow}>
              <Text style={styles.questionNumber}>{i + 1}.</Text>
              <Text style={styles.questionText}>{question}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Conversation Strategy */}
      {content.conversation_strategy ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Conversation Strategy</Text>
          <View style={styles.strategyBox}>
            <Text style={styles.strategyText}>
              {content.conversation_strategy}
            </Text>
          </View>
        </View>
      ) : null}
    </ArtifactCard>
  );
}

const styles = StyleSheet.create({
  section: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  summaryText: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 21,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
    marginRight: spacing.sm,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  questionRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  questionNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
    marginRight: spacing.sm,
    lineHeight: 20,
    width: 18,
  },
  questionText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  strategyBox: {
    backgroundColor: colors.primaryLight,
    borderRadius: 8,
    padding: spacing.sm,
  },
  strategyText: {
    fontSize: 14,
    color: colors.primary,
    lineHeight: 20,
    fontWeight: '500',
  },
});
