import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { Account } from '../services/types';
import { listAccounts, captureFile, accountFromCapture } from '../services/api';
import SearchBar from '../components/SearchBar';
import AccountListItem from '../components/AccountListItem';

export default function HomeScreen() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const loadAccounts = useCallback(async () => {
    try {
      setLoading(true);
      const result = await listAccounts(20);
      setAccounts(result.accounts);
    } catch (err) {
      // Silently fail — show empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  const handleAccountSelect = useCallback(
    (account: Account) => {
      router.push(`/account/${account.id}`);
    },
    [router]
  );

  const handleUploadScreenshot = useCallback(async () => {
    try {
      const permissionResult =
        await ImagePicker.requestMediaLibraryPermissionsAsync();

      if (!permissionResult.granted) {
        Alert.alert(
          'Permission Required',
          'Please allow access to your photo library to upload screenshots.'
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality: 0.8,
      });

      if (result.canceled || !result.assets?.length) {
        return;
      }

      setUploading(true);
      const asset = result.assets[0];

      const file = {
        uri: asset.uri,
        type: asset.mimeType || 'image/jpeg',
        name: asset.fileName || 'screenshot.jpg',
      };

      const captureResult = await captureFile(file);

      const accountResult = await accountFromCapture({
        ingestion_event_id: captureResult.ingestion_event_id,
      });

      router.push(`/account/${accountResult.account.id}`);
    } catch (err: any) {
      Alert.alert('Upload Failed', err.message || 'Could not process the image.');
    } finally {
      setUploading(false);
    }
  }, [router]);

  const handleNewAccount = useCallback(() => {
    router.push('/account/new');
  }, [router]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <SearchBar onSelectAccount={handleAccountSelect} />

      <View style={styles.actions}>
        <Pressable
          style={[styles.actionButton, styles.actionUpload]}
          onPress={handleUploadScreenshot}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator color={colors.primary} size="small" />
          ) : (
            <>
              <Text style={styles.actionIcon}>{'[ ]'}</Text>
              <Text style={styles.actionLabel}>Upload Screenshot</Text>
            </>
          )}
        </Pressable>

        <Pressable
          style={[styles.actionButton, styles.actionNew]}
          onPress={handleNewAccount}
        >
          <Text style={styles.actionIconDark}>+</Text>
          <Text style={styles.actionLabelDark}>New Account</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Accounts</Text>

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator color={colors.primary} size="large" />
          </View>
        ) : accounts.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No accounts yet</Text>
            <Text style={styles.emptySubtitle}>
              Upload a screenshot or create a new account to get started.
            </Text>
          </View>
        ) : (
          accounts.map((account) => (
            <AccountListItem
              key={account.id}
              account={account}
              onPress={() => handleAccountSelect(account)}
            />
          ))
        )}
      </View>
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
  actions: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
    marginBottom: spacing.lg,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: spacing.md,
    borderRadius: 12,
    gap: spacing.sm,
  },
  actionUpload: {
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  actionNew: {
    backgroundColor: colors.primary,
  },
  actionIcon: {
    fontSize: 16,
    color: colors.primary,
    fontWeight: '600',
  },
  actionIconDark: {
    fontSize: 20,
    color: colors.surface,
    fontWeight: '700',
  },
  actionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.primary,
  },
  actionLabelDark: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.surface,
  },
  section: {
    marginTop: spacing.sm,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  loadingContainer: {
    paddingVertical: spacing.xl,
    alignItems: 'center',
  },
  emptyState: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  emptySubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
});
