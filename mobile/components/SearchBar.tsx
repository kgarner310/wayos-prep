import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  Pressable,
  FlatList,
} from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { Account } from '../services/types';
import { searchAccounts } from '../services/api';

interface SearchBarProps {
  onSelectAccount: (account: Account) => void;
}

export default function SearchBar({ onSelectAccount }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Account[]>([]);
  const [showResults, setShowResults] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearch = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }

    try {
      const data = await searchAccounts(q.trim());
      setResults(data.accounts);
      setShowResults(data.accounts.length > 0);
    } catch {
      setResults([]);
      setShowResults(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      handleSearch(query);
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, handleSearch]);

  const handleSelect = useCallback(
    (account: Account) => {
      setQuery('');
      setResults([]);
      setShowResults(false);
      onSelectAccount(account);
    },
    [onSelectAccount]
  );

  const handleBlur = useCallback(() => {
    // Delay hiding so tap on result registers
    setTimeout(() => setShowResults(false), 200);
  }, []);

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        value={query}
        onChangeText={setQuery}
        placeholder="Search accounts..."
        placeholderTextColor={colors.textSecondary}
        onFocus={() => results.length > 0 && setShowResults(true)}
        onBlur={handleBlur}
        returnKeyType="search"
        autoCorrect={false}
        autoCapitalize="none"
      />

      {showResults && (
        <View style={styles.dropdown}>
          <FlatList
            data={results}
            keyExtractor={(item) => item.id}
            keyboardShouldPersistTaps="handled"
            style={styles.resultList}
            renderItem={({ item }) => (
              <Pressable
                style={styles.resultItem}
                onPress={() => handleSelect(item)}
              >
                <Text style={styles.resultName}>{item.account_name}</Text>
                <Text style={styles.resultMeta}>
                  {[item.industry, item.state].filter(Boolean).join(' \u00B7 ')}
                </Text>
              </Pressable>
            )}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    zIndex: 10,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  dropdown: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    marginTop: 4,
    maxHeight: 240,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  resultList: {
    borderRadius: 12,
  },
  resultItem: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  resultName: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
  },
  resultMeta: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
});
