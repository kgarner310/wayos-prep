import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
  TouchableOpacity,
  Share,
} from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { useLocalSearchParams } from 'expo-router';
import { api, BriefResponse } from '../../services/api';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Section } from '../../components/Section';
import { colors, spacing } from '../../services/theme';

export default function BriefScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [brief, setBrief] = useState<BriefResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSendPack, setShowSendPack] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(false);

  useEffect(() => {
    if (id) {
      api
        .getBrief(parseInt(id, 10))
        .then(setBrief)
        .catch((err) => Alert.alert('Error', err.message))
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleCopy = async () => {
    if (!brief) return;
    await Clipboard.setStringAsync(brief.brief_text);
    Alert.alert('Copied', 'Brief copied to clipboard.');
  };

  const handleShare = async () => {
    if (!brief) return;
    try {
      await Share.share({
        message: brief.brief_text,
        title: `WAYOS PREP — ${brief.brief_json.industry}`,
      });
    } catch {}
  };

  const handleShareEmail = async () => {
    if (!brief) return;
    setShowSendPack(false);
    try {
      await Share.share({
        message: brief.underwriter_email_text,
        title: `${brief.brief_json.industry} Risk Notes`,
      });
    } catch {}
  };

  const handleShareNote = async () => {
    if (!brief) return;
    setShowSendPack(false);
    try {
      await Share.share({
        message: brief.internal_note_text,
        title: `WAYOS PREP — Account Prep`,
      });
    } catch {}
  };

  const handleFeedback = async (helpful: boolean) => {
    if (!brief || feedbackGiven) return;
    try {
      await api.submitFeedback({
        query_log_id: brief.id,
        helpful_bool: helpful,
      });
      setFeedbackGiven(true);
      Alert.alert('Thanks!', 'Your feedback helps improve WAYOS PREP.');
    } catch {}
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!brief) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Brief not found.</Text>
      </View>
    );
  }

  const bj = brief.brief_json;

  return (
    <>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
      >
        <Card style={styles.headerCard}>
          <Text style={styles.brandLabel}>WAYOS PREP — CLIENT BRIEF</Text>
          <Text style={styles.industry}>{bj.industry}</Text>
          <View style={styles.metaRow}>
            <Text style={styles.meta}>{bj.location}</Text>
            {bj.employee_count && (
              <Text style={styles.meta}> • {bj.employee_count} employees</Text>
            )}
          </View>
          {(bj.mod || bj.vehicle_exposure) && (
            <View style={styles.metaRow}>
              {bj.mod && <Text style={styles.meta}>MOD: {bj.mod}</Text>}
              {bj.vehicle_exposure && (
                <Text style={styles.meta}>
                  {bj.mod ? ' • ' : ''}Vehicles: {bj.vehicle_exposure}
                </Text>
              )}
            </View>
          )}
          <Text style={styles.timestamp}>{bj.generated_at}</Text>
        </Card>

        <Card>
          <Section
            title="Top Claim Drivers (what actually hurts)"
            items={bj.top_claim_drivers}
          />
          <Section
            title="Regional / Local Risk Notes"
            text={bj.regional_risk_notes}
          />
          <Section
            title="Coverage Exposures (what to stress-test)"
            items={bj.coverage_exposures}
          />
          <Section
            title="Conversation Starters (producer ammo)"
            items={bj.conversation_starters}
          />
          <Section
            title="Quick Docs to Request"
            items={bj.docs_to_request}
          />
        </Card>

        <View style={styles.actions}>
          <Button title="Copy Brief" onPress={handleCopy} variant="secondary" />
          <Button
            title="Share Brief"
            onPress={handleShare}
            variant="primary"
            style={styles.actionSpacing}
          />
          <Button
            title="Send Pack"
            onPress={() => setShowSendPack(true)}
            variant="outline"
            style={styles.actionSpacing}
          />
        </View>

        {!feedbackGiven && (
          <Card style={styles.feedbackCard}>
            <Text style={styles.feedbackTitle}>Was this brief helpful?</Text>
            <View style={styles.feedbackRow}>
              <TouchableOpacity
                style={styles.feedbackBtn}
                onPress={() => handleFeedback(true)}
              >
                <Text style={styles.feedbackEmoji}>👍</Text>
                <Text style={styles.feedbackLabel}>Helpful</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.feedbackBtn}
                onPress={() => handleFeedback(false)}
              >
                <Text style={styles.feedbackEmoji}>👎</Text>
                <Text style={styles.feedbackLabel}>Not Helpful</Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}

        {feedbackGiven && (
          <Card style={styles.feedbackCard}>
            <Text style={styles.feedbackThanks}>Thanks for your feedback!</Text>
          </Card>
        )}

        <Text style={styles.watermark}>
          Prepared with WAYOS PREP • wayosprep.app
        </Text>
      </ScrollView>

      <Modal visible={showSendPack} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Send Pack</Text>
            <Text style={styles.modalHint}>
              Share pre-formatted messages with your team.
            </Text>

            <Button
              title="Send Underwriter Email"
              onPress={handleShareEmail}
              variant="primary"
              style={styles.modalBtn}
            />
            <Button
              title="Send Internal Note"
              onPress={handleShareNote}
              variant="secondary"
              style={styles.modalBtn}
            />
            <Button
              title="Cancel"
              onPress={() => setShowSendPack(false)}
              variant="outline"
              style={styles.modalBtn}
            />
          </View>
        </View>
      </Modal>
    </>
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
  errorText: {
    fontSize: 16,
    color: colors.error,
  },
  headerCard: {
    marginBottom: spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: colors.accent,
  },
  brandLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.accent,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: spacing.xs,
  },
  industry: {
    fontSize: 26,
    fontWeight: '800',
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  metaRow: {
    flexDirection: 'row',
    marginBottom: 2,
  },
  meta: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  timestamp: {
    fontSize: 12,
    color: colors.textLight,
    marginTop: spacing.xs,
  },
  actions: {
    marginTop: spacing.lg,
  },
  actionSpacing: {
    marginTop: spacing.sm + 4,
  },
  feedbackCard: {
    marginTop: spacing.lg,
    alignItems: 'center',
  },
  feedbackTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.md,
  },
  feedbackRow: {
    flexDirection: 'row',
    gap: spacing.xl,
  },
  feedbackBtn: {
    alignItems: 'center',
  },
  feedbackEmoji: {
    fontSize: 32,
  },
  feedbackLabel: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  feedbackThanks: {
    fontSize: 16,
    color: colors.success,
    fontWeight: '600',
  },
  watermark: {
    textAlign: 'center',
    fontSize: 12,
    color: colors.textLight,
    marginTop: spacing.lg,
    marginBottom: spacing.xxl,
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
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  modalHint: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  modalBtn: {
    marginBottom: spacing.sm,
  },
});
