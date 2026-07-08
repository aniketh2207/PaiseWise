// app/index.tsx
import { Redirect } from 'expo-router';

export default function AppRoot() {
  // Instantly redirects the app into the dashboard screen on startup
  return <Redirect href="/(tabs)/dashboard" />;
}