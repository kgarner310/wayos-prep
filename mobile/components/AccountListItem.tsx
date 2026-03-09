import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { Account } from '../services/types';

interface AccountListItemProps {
  account: Account;
  onPress: () => void;
}

export default function AccountListItem({
  account,
  onPress,
}: AccountListItemProps) {
  return (
    <Pressable
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
      onPress={onPress}
    >
      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={1}>
          {account.account_name}
        </Text>
        <Text style={styles.meta} numberOfLines={1}>
          {[account.industry, account.state].filter(Boolean).join(' \u00B7 ')}
        </Text>
      </View>
      <Text style={styles.chevron}>{'\u203A'}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 10,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  pressed: {
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
  },
  name: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
  },
  meta: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  chevron: {
    fontSize: 24,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
    fontWeight: '300',
  },
});
