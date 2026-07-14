import { Tabs, usePathname, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, StyleSheet, Text, PanResponder } from 'react-native';
import { useRef } from 'react';

export default function TabLayout() {
  const pathname = usePathname();
  const router = useRouter();

  // Tab routes sequence in the bottom bar layout
  const routeOrder = ['/dashboard', '/queue', '/upload', '/reports'];

  // Handle page transitions based on horizontal swipe action
  const handleSwipe = (direction: 'left' | 'right') => {
    const currentIdx = routeOrder.indexOf(pathname);
    if (currentIdx === -1) return;

    if (direction === 'left' && currentIdx < routeOrder.length - 1) {
      router.replace(routeOrder[currentIdx + 1] as any);
    } else if (direction === 'right' && currentIdx > 0) {
      router.replace(routeOrder[currentIdx - 1] as any);
    }
  };

  // Configure gesture responder to detect horizontal swipes
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponderCapture: (_, gestureState) => {
        // Intercept horizontal gestures before they reach child scroll views
        return Math.abs(gestureState.dx) > 50 && Math.abs(gestureState.dy) < 15;
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dx > 50) {
          handleSwipe('right');
        } else if (gestureState.dx < -50) {
          handleSwipe('left');
        }
      },
    })
  ).current;

  // Helper to dynamically compile screen options for active popping tabs
  const getScreenOptions = (
    title: string,
    activeIcon: keyof typeof Ionicons.glyphMap,
    inactiveIcon: keyof typeof Ionicons.glyphMap
  ) => ({
    title,
    tabBarLabel: ({ focused, color }: { focused: boolean; color: any }) => 
      focused ? null : (
        <Text style={[styles.tabBarLabel, { color }]}>{title}</Text>
      ),
    tabBarIcon: ({ color, focused }: { color: any; focused: boolean }) => (
      <View style={focused ? styles.fabContainer : styles.normalIconContainer}>
        <Ionicons 
          name={focused ? activeIcon : inactiveIcon} 
          size={focused ? 24 : 22} 
          color={focused ? '#FFFFFF' : color} 
        />
      </View>
    ),
  });

  return (
    <View style={styles.rootContainer} {...panResponder.panHandlers}>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarShowLabel: true, // Restore tab names/labels
          tabBarActiveTintColor: '#34D399', // mint/green active icon
          tabBarInactiveTintColor: '#94A3B8', // soft slate inactive icon
          tabBarStyle: styles.tabBar,
        }}
      >
        <Tabs.Screen
          name="dashboard"
          options={getScreenOptions('Dashboard', 'pie-chart', 'pie-chart-outline')}
        />
        <Tabs.Screen
          name="queue"
          options={getScreenOptions('Queue', 'list', 'list-outline')}
        />
        <Tabs.Screen
          name="upload"
          options={getScreenOptions('Upload', 'cloud-upload', 'cloud-upload-outline')}
        />
        <Tabs.Screen
          name="reports"
          options={getScreenOptions('Reports', 'document-text', 'document-text-outline')}
        />
      </Tabs>
    </View>
  );
}

const styles = StyleSheet.create({
  rootContainer: {
    flex: 1,
  },
  tabBar: {
   position: 'absolute',
    bottom: 24,
    left: 0,
    right: 0,
    marginHorizontal: 20, // Forces exactly 20px of space on both sides
    backgroundColor: '#0F172A', 
    borderRadius: 24,
    height: 70, 
    borderWidth: 1,
    borderColor: '#1E293B',
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.2,
    shadowRadius: 15,
    elevation: 8,
    paddingBottom: 6,
    paddingTop: 8,
    overflow: 'visible',
  },
  tabBarLabel: {
    fontSize: 10,
    fontWeight: '700',
    marginTop: 2,
  },
  normalIconContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    height: 38,
  },
  fabContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#059669', // Emerald Green brand FAB
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: -22, // Popping vertical offset above the tab bar top boundary
    borderWidth: 3,
    borderColor: '#0F172A', // Seamless outer border ring matching the tab bar color (integrated cut-out)
    shadowColor: '#059669',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 5,
  },
});