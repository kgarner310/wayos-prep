import React from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { colors } from '../theme/colors';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: colors.surface,
          },
          headerTintColor: colors.text,
          headerTitleStyle: {
            fontWeight: '700',
            fontSize: 18,
          },
          headerShadowVisible: false,
          contentStyle: {
            backgroundColor: colors.background,
          },
        }}
      >
        <Stack.Screen
          name="index"
          options={{
            title: 'WAYOS',
            headerTitleStyle: {
              fontWeight: '800',
              fontSize: 22,
              color: colors.primary,
            },
          }}
        />
        <Stack.Screen
          name="account/[id]"
          options={{
            title: 'Account Dashboard',
          }}
        />
        <Stack.Screen
          name="account/new"
          options={{
            title: 'New Account',
            presentation: 'modal',
          }}
        />
        <Stack.Screen
          name="outcome/[id]"
          options={{
            title: 'Log Outcome',
            presentation: 'modal',
          }}
        />
      </Stack>
    </SafeAreaProvider>
  );
}
