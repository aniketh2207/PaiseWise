import { View, Text, StyleSheet, Pressable, ScrollView, ActivityIndicator, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState, useCallback, useEffect } from 'react';
import { useFocusEffect } from 'expo-router';
import axios from 'axios';
import { API_ROUTES } from '../../constants/api';
import { dashboardCache } from '../../utils/dashboardCache';

interface Summary {
  exists: boolean;
  total_debits: number;
  total_credits: number;
  by_category: Record<string, number>;
  top_merchant: string | null;
  match_rate: number;
  pending_annotations: number;
  llm_summary?: any;
}

export default function Dashboard() {
  const router = useRouter();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  // State for Month and Year (default to current month & year)
  // State for Month and Year (null defaults to latest month with data)
  const [month, setMonth] = useState<number | null>(null);
  const [year, setYear] = useState<number | null>(null);

  const monthsList = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handlePrevMonth = () => {
    const curM = month || (new Date().getMonth() + 1);
    const curY = year || new Date().getFullYear();
    if (curM === 1) {
      setMonth(12);
      setYear(curY - 1);
    } else {
      setMonth(curM - 1);
    }
  };

  const handleNextMonth = () => {
    const curM = month || (new Date().getMonth() + 1);
    const curY = year || new Date().getFullYear();
    if (curM === 12) {
      setMonth(1);
      setYear(curY + 1);
    } else {
      setMonth(curM + 1);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await get_summary(month, year, true);
    } catch (err) {
      console.log(err);
    } finally {
      setRefreshing(false);
    }
  }, [month, year]);

  const get_summary = async (targetMonth?: number | null, targetYear?: number | null, force: boolean = false) => {
    const cacheKey = `${targetYear || 'default'}-${targetMonth || 'default'}`;
    if (!force && !dashboardCache.needsRefresh && dashboardCache.cache[cacheKey]) {
      setSummary(dashboardCache.cache[cacheKey]);
      setLoading(false);
      setError("");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSummary(null);
      const params: any = {};
      if (targetMonth) params.month = targetMonth;
      if (targetYear) params.year = targetYear;

      const response = await axios.get(API_ROUTES.dashboardSummary, { params });
      setSummary(response.data);
      if (response.data.month && response.data.year) {
        setMonth(response.data.month);
        setYear(response.data.year);
      }
      dashboardCache.cache[cacheKey] = response.data;
      dashboardCache.needsRefresh = false;
    } catch (err) {
      console.log(err);
      setError('Failed to fetch summary');
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      get_summary(month, year, false);
    }, [month, year])
  );

  if (loading && !summary) {
    return (
      <SafeAreaView style={[styles.container, styles.centerContainer]}>
        <ActivityIndicator size="large" color="#059669" />
        <Text style={styles.loadingText}>Loading Dashboard...</Text>
      </SafeAreaView>
    );
  }

  if (error && !summary) {
    return (
      <SafeAreaView style={[styles.container, styles.centerContainer]}>
        <Ionicons name="alert-circle-outline" size={48} color="#EF4444" />
        <Text style={styles.errorText}>{error}</Text>
        <Pressable style={styles.retryButton} onPress={() => get_summary(month, year, true)}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  const hasData = summary && summary.exists;
  const totalTracked = hasData ? (summary.total_debits + summary.total_credits) : 0;
  const totalIncome = hasData ? summary.total_credits : 0;
  const totalExpense = hasData ? summary.total_debits : 0;
  
  const insightsText = hasData 
    ? summary.llm_summary 
    : "No statement data found. Go to 'Upload PDF' to import your bank transactions and generate AI insights!";

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl 
            refreshing={refreshing} 
            onRefresh={onRefresh} 
            colors={["#059669"]} 
            tintColor="#059669" 
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.welcomeText}>Hello there 👋</Text>
            <Text style={styles.appName}>paiseWise</Text>
          </View>
          <Pressable style={styles.profileBadge}>
            <Ionicons name="person-circle-outline" size={32} color="#059669" />
          </Pressable>
        </View>

        {/* Period Navigation Selector */}
        <View style={styles.periodCard}>
          <Pressable style={styles.arrowButton} onPress={handlePrevMonth}>
            <Ionicons name="chevron-back" size={20} color="#059669" />
          </Pressable>
          <View style={styles.periodTextContainer}>
            <Ionicons name="calendar" size={16} color="#059669" style={{ marginRight: 8 }} />
            <Text style={styles.periodLabel}>
              {month ? `${monthsList[month - 1]} ${year}` : 'Loading...'}
            </Text>
          </View>
          <Pressable style={styles.arrowButton} onPress={handleNextMonth}>
            <Ionicons name="chevron-forward" size={20} color="#059669" />
          </Pressable>
        </View>

        {/* Balance Card */}
        <View style={styles.heroCard}>
          <Text style={styles.heroLabel}>Total Tracked Transactions</Text>
          <Text style={styles.heroAmount}>
            ₹{totalTracked.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Text>
          <View style={styles.heroMeta}>
            <View style={styles.metaItem}>
              <Ionicons name="arrow-down-circle" size={18} color="#10B981" />
              <Text style={styles.metaText}>
                Income: ₹{totalIncome.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="arrow-up-circle" size={18} color="#EF4444" />
              <Text style={styles.metaText}>
                Expenses: ₹{totalExpense.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </Text>
            </View>
          </View>
        </View>

        {/* Pending Banner Alert */}
        {hasData && summary.pending_annotations > 0 && (
          <Pressable style={styles.pendingBanner} onPress={() => router.push('/queue')}>
            <Ionicons name="information-circle" size={20} color="#D97706" />
            <Text style={styles.pendingBannerText}>
              You have {summary.pending_annotations} transactions pending annotation. Tap to resolve.
            </Text>
            <Ionicons name="chevron-forward" size={16} color="#D97706" />
          </Pressable>
        )}

        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionGrid}>
          <Pressable style={styles.actionCard} onPress={() => router.push('/upload')}>
            <View style={[styles.actionIconContainer, { backgroundColor: '#ECFDF5' }]}>
              <Ionicons name="cloud-upload" size={24} color="#10B981" />
            </View>
            <Text style={styles.actionTitle}>Upload PDF</Text>
            <Text style={styles.actionDesc}>Import statement</Text>
          </Pressable>

          <Pressable style={styles.actionCard} onPress={() => router.push('/queue')}>
            <View style={[styles.actionIconContainer, { backgroundColor: '#F0FDF4' }]}>
              <Ionicons name="clipboard" size={24} color="#10B981" />
            </View>
            <Text style={styles.actionTitle}>Verify Queue</Text>
            <Text style={styles.actionDesc}>Annotate items</Text>
          </Pressable>
        </View>

        {/* Summary Card */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <Ionicons name="sparkles" size={20} color="#059669" />
            <Text style={styles.summaryTitle}>AI Expense Insights</Text>
          </View>
          <Text style={styles.summaryText}>
            {typeof insightsText === 'string' 
              ? insightsText 
              : (Array.isArray(insightsText) 
                  ? insightsText.map(b => b?.text || '').join('') 
                  : (insightsText?.text || JSON.stringify(insightsText)))}
          </Text>
        </View>

        {/* Category Breakdown */}
        {hasData && Object.keys(summary.by_category).length > 0 && (
          <View style={styles.categoryCard}>
            <Text style={styles.categoryCardTitle}>Category Breakdown</Text>
            {Object.entries(summary.by_category)
              .sort((a, b) => b[1] - a[1])
              .map(([category, amount]) => {
                const percentage = totalExpense > 0 ? (amount / totalExpense) * 100 : 0;
                return (
                  <View key={category} style={styles.categoryRow}>
                    <View style={styles.categoryInfo}>
                      <Text style={styles.categoryName}>{category}</Text>
                      <Text style={styles.categoryAmount}>
                        ₹{amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </Text>
                    </View>
                    <View style={styles.progressBarBg}>
                      <View style={[styles.progressBarFill, { width: `${percentage}%` }]} />
                    </View>
                  </View>
                );
              })}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 110,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  welcomeText: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0F172A',
  },
  profileBadge: {
    padding: 4,
  },
  heroCard: {
    backgroundColor: '#0F172A',
    borderRadius: 24,
    padding: 24,
    marginBottom: 28,
    // Soft shadow
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.1,
    shadowRadius: 15,
    elevation: 5,
  },
  heroLabel: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  heroAmount: {
    color: '#FFFFFF',
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  heroMeta: {
    flexDirection: 'row',
    gap: 16,
    borderTopWidth: 1,
    borderTopColor: '#334155',
    paddingTop: 16,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    color: '#E2E8F0',
    fontSize: 13,
    fontWeight: '500',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 16,
  },
  actionGrid: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 28,
  },
  actionCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    // Soft shadow
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.03,
    shadowRadius: 10,
    elevation: 1,
  },
  actionIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  actionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  actionDesc: {
    fontSize: 12,
    color: '#64748B',
  },
  summaryCard: {
    backgroundColor: '#F1F5F9',
    borderRadius: 20,
    padding: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#059669',
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  summaryTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  summaryText: {
    fontSize: 13,
    lineHeight: 20,
    color: '#475569',
  },
  centerContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
  },
  errorText: {
    marginTop: 12,
    fontSize: 15,
    color: '#64748B',
    fontWeight: '500',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#059669',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 12,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  pendingBanner: {
    backgroundColor: '#FEF3C7',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  pendingBannerText: {
    flex: 1,
    fontSize: 13,
    fontWeight: '600',
    color: '#92400E',
  },
  categoryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 24,
    marginTop: 24,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.03,
    shadowRadius: 10,
    elevation: 1,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  categoryCardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 16,
  },
  categoryRow: {
    marginBottom: 16,
  },
  categoryInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
  },
  categoryAmount: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0F172A',
  },
  progressBarBg: {
    height: 8,
    backgroundColor: '#F1F5F9',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#059669',
    borderRadius: 4,
  },
  periodCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.03,
    shadowRadius: 10,
    elevation: 2,
    marginBottom: 24,
  },
  arrowButton: {
    width: 38,
    height: 38,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
  },
  periodTextContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  periodLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
});
