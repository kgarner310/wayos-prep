import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { colors } from '../services/theme';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.primary },
          headerTintColor: colors.white,
          headerTitleStyle: { fontWeight: '700' },
          headerBackTitleVisible: false,
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen
          name="index"
          options={{ title: 'WAYOS PREP', headerTitleAlign: 'center' }}
        />
        <Stack.Screen name="ask" options={{ title: 'Ask Risk Question' }} />
        <Stack.Screen name="prep" options={{ title: 'Prep This Account' }} />
        <Stack.Screen name="lookup" options={{ title: 'Industry Lookup' }} />
        <Stack.Screen name="industry/[id]" options={{ title: 'Industry Detail' }} />
        <Stack.Screen name="brief/[id]" options={{ title: 'Client Brief' }} />
      </Stack>
    </>
  );
}
