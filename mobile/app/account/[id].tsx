import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { colors } from '../../theme/colors';
import { spacing } from '../../theme/spacing';
import {
  DashboardResponse,
  Artifact,
  CoverageGapArtifact,
  MeetingBriefArtifact,
  WorkersCompSnapshotArtifact,
  WinnabilityArtifact,
} from '../../services/types';
import { getAccountDashboard, generateArtifacts } from '../../services/api';
import HealthCard from '../../components/HealthCard';
import CoverageGapCard from '../../components/CoverageGapCard';
import MeetingBriefCard from '../../components/MeetingBriefCard';
import WorkersCompCard from '../../components/WorkersCompCard';
import WinnabilityCard from '../../components/WinnabilityCard';
import InsightFeed from '../../components/InsightFeed';
import LoadingCard from '../../components/LoadingCard';

function findArtifact(artifacts: Artifact[], type: string): Artifact | undefined {
  return artifacts.find((a) => a.artifact_type === type);
}

export default function AccountDashboard() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDashboard = useCallback(
    async (silent = false) => {
      if (!id) return;
      try {
        if (!silent) setLoading(true);
        const data = await getAccountDashboard(id);
        setDashboard(data);
        setError(null);
      } catch (err: any) {
        if (!silent) setError(err.message || 'Failed to load dashboard');
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [id]
  );

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Poll while any artifact is pending
  useEffect(() => {
    const hasPending = dashboard?.artifacts?.some((a) => a.status === 'pending');

    if (hasPending) {
      pollRef.current = setInterval(() => {
        fetchDashboard(true);
      }, 3000);
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [dashboard, fetchDashboard]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchDashboard(true);
    setRefreshing(false);
  }, [fetchDashboard]);

  const handleGenerateArtifacts = useCallback(async () => {
    if (!id) return;
    try {
      await generateArtifacts(id);
      await fetchDashboard();
    } catch {
      // ignore
    }
  }, [id, fetchDashboard]);

  if (loading) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <LoadingCard />
        <LoadingCard />
        <LoadingCard />
      </ScrollView>
    );
  }

  if (error || !dashboard) {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.errorText}>{error || 'Dashboard not found'}</Text>
        <Pressable style={styles.retryButton} onPress={() => fetchDashboard()}>
          <Text style={styles.retryText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  const { account, health, artifacts, insights } = dashboard;

  const coverageGap = findArtifact(artifacts, 'coverage_gap');
  const meetingBrief = findArtifact(artifacts, 'meeting_brief');
  const workersComp = findArtifact(artifacts, 'workers_comp_snapshot');
  const winnability = findArtifact(artifacts, 'winnability');

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Account Header */}
      <View style={styles.accountHeader}>
        <Text style={styles.accountName}>{account.account_name}</Text>
        {account.named_insured && account.named_insured !== account.account_name && (
          <Text style={styles.namedInsured}>{account.named_insured}</Text>
        )}
        <View style={styles.metaRow}>
          {account.industry ? (
            <View style={styles.metaTag}>
              <Text style={styles.metaTagText}>{account.industry}</Text>
            </View>
          ) : null}
          {account.state ? (
            <View style={styles.metaTag}>
              <Text style={styles.metaTagText}>{account.state}</Text>
            </View>
          ) : null}
          {account.employee_count ? (
            <View style={styles.metaTag}>
              <Text style={styles.metaTagText}>
                {account.employee_count} employees
              </Text>
            </View>
          ) : null}
        </View>
      </View>

      {/* Health Card */}
      <HealthCard health={health} />

      {/* Generate Artifacts button if none exist */}
      {artifacts.length === 0 && (
        <Pressable style={styles.generateButton} onPress={handleGenerateArtifacts}>
          <Text style={styles.generateButtonText}>Generate Artifacts</Text>
        </Pressable>
      )}

      {/* Coverage Gap */}
      {coverageGap &&
        (coverageGap.status === 'pending' ? (
          <LoadingCard label="Analyzing coverage gaps..." />
        ) : coverageGap.status === 'ready' && coverageGap.content_json ? (
          <CoverageGapCard
            artifact={coverageGap}
            content={coverageGap.content_json as unknown as CoverageGapArtifact}
          />
        ) : null)}

      {/* Meeting Brief */}
      {meetingBrief &&
        (meetingBrief.status === 'pending' ? (
          <LoadingCard label="Preparing meeting brief..." />
        ) : meetingBrief.status === 'ready' && meetingBrief.content_json ? (
          <MeetingBriefCard
            artifact={meetingBrief}
            content={meetingBrief.content_json as unknown as MeetingBriefArtifact}
          />
        ) : null)}

      {/* Workers Comp */}
      {workersComp &&
        (workersComp.status === 'pending' ? (
          <LoadingCard label="Analyzing workers comp..." />
        ) : workersComp.status === 'ready' && workersComp.content_json ? (
          <WorkersCompCard
            artifact={workersComp}
            content={
              workersComp.content_json as unknown as WorkersCompSnapshotArtifact
            }
          />
        ) : null)}

      {/* Winnability */}
      {winnability &&
        (winnability.status === 'pending' ? (
          <LoadingCard label="Calculating winnability..." />
        ) : winnability.status === 'ready' && winnability.content_json ? (
          <WinnabilityCard
            artifact={winnability}
            content={winnability.content_json as unknown as WinnabilityArtifact}
          />
        ) : null)}

      {/* Insights */}
      {insights && insights.length > 0 && <InsightFeed insights={insights} />}

      {/* Outcome Button */}
      <Pressable
        style={styles.outcomeButton}
        onPress={() => router.push(`/outcome/${id}`)}
      >
        <Text style={styles.outcomeButtonText}>Log Outcome</Text>
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
  center: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  accountHeader: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  accountName: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 2,
  },
  namedInsured: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  metaTag: {
    backgroundColor: colors.background,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 6,
  },
  metaTagText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  generateButton: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  generateButtonText: {
    color: colors.surface,
    fontSize: 16,
    fontWeight: '600',
  },
  outcomeButton: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.primary,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: spacing.md,
  },
  outcomeButtonText: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
  errorText: {
    fontSize: 16,
    color: colors.danger,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: spacing.lg,
  },
  retryText: {
    color: colors.surface,
    fontSize: 14,
    fontWeight: '600',
  },
  bottomSpacer: {
    height: spacing.xl,
  },
});
