import { View, Text, StyleSheet, Pressable, ScrollView, ActivityIndicator, TextInput, Linking, Alert, RefreshControl, Platform, KeyboardAvoidingView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useState, useCallback, useEffect } from 'react';
import { useFocusEffect, useRouter } from 'expo-router';
import axios from 'axios';
import { API_ROUTES } from '../../constants/api';

interface Recipient {
  id: number;
  name: string;
  email: string;
  active: boolean;
}

export default function Reports() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  // State for Month and Year (default to current month & year)
  const currentDate = new Date();
  const [month, setMonth] = useState<number>(currentDate.getMonth() + 1);
  const [year, setYear] = useState<number>(currentDate.getFullYear());
  
  // State for report data
  const [insights, setInsights] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [errorText, setErrorText] = useState<string>('');
  
  // State for recipients
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [newRecipName, setNewRecipName] = useState<string>('');
  const [newRecipEmail, setNewRecipEmail] = useState<string>('');
  const [addingRecip, setAddingRecip] = useState<boolean>(false);
  const [sending, setSending] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        fetchReport(month, year, true),
        fetchRecipients()
      ]);
    } catch (err) {
      console.log(err);
    } finally {
      setRefreshing(false);
    }
  }, [month, year]);

  // Period Selector Utilities
  const monthsList = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handlePrevMonth = () => {
    if (month === 1) {
      setMonth(12);
      setYear(prev => prev - 1);
    } else {
      setMonth(prev => prev - 1);
    }
  };

  const handleNextMonth = () => {
    if (month === 12) {
      setMonth(1);
      setYear(prev => prev + 1);
    } else {
      setMonth(prev => prev + 1);
    }
  };

  // Helper to extract initials for avatar circles
  const getInitials = (name: string) => {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  // API Call: Fetch Report (Insights and check if generated)
  const fetchReport = async (targetMonth: number, targetYear: number, forceRefresh: boolean = false) => {
    try {
      setLoading(true);
      setErrorText('');
      setInsights('');
      
      const response = await axios.get(API_ROUTES.generateReport, {
        params: { month: targetMonth, year: targetYear, refresh: forceRefresh }
      });
      
      if (response.data.status === 'success') {
        setInsights(response.data.insights || 'No insights compiled.');
      } else {
        setErrorText(response.data.error || 'Failed to retrieve report.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'No statement data has been reconciled for this period yet.';
      setErrorText(msg);
    } finally {
      setLoading(false);
    }
  };

  // API Call: Fetch Recipients List
  const fetchRecipients = async () => {
    try {
      const response = await axios.get(API_ROUTES.recipients);
      setRecipients(response.data || []);
    } catch (err) {
      console.log('Failed to fetch recipients', err);
    }
  };

  // API Call: Add New Email Recipient
  const handleAddRecipient = async () => {
    if (!newRecipName.trim() || !newRecipEmail.trim()) {
      Alert.alert('Validation Error', 'Please enter both a name and an email address.');
      return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newRecipEmail)) {
      Alert.alert('Validation Error', 'Please enter a valid email address.');
      return;
    }

    try {
      setAddingRecip(true);
      await axios.post(API_ROUTES.recipients, {
        name: newRecipName.trim(),
        email: newRecipEmail.trim(),
      });
      
      setNewRecipName('');
      setNewRecipEmail('');
      fetchRecipients();
      Alert.alert('Success', 'Recipient added successfully.');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to add recipient.';
      Alert.alert('Error', msg);
    } finally {
      setAddingRecip(false);
    }
  };

  // API Call: Delete/Deactivate Recipient
  const handleDeleteRecipient = async (id: number) => {
    Alert.alert(
      'Remove Recipient',
      'Are you sure you want to stop sending monthly reports to this email?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Remove', 
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(API_ROUTES.deleteRecipient(id));
              fetchRecipients();
            } catch (err: any) {
              Alert.alert('Error', 'Failed to remove recipient.');
            }
          }
        }
      ]
    );
  };

  // API Call: Download Excel Spreadsheet Report
  const handleDownload = () => {
    const downloadUrl = `${API_ROUTES.downloadReport}?month=${month}&year=${year}`;
    Linking.openURL(downloadUrl).catch(() => {
      Alert.alert('Error', 'Failed to open report download URL.');
    });
  };

  // API Call: Dispatch Email
  const handleSendEmail = async () => {
    if (recipients.length === 0) {
      Alert.alert('Recipients Required', 'You must configure at least one active recipient before dispatching reports.');
      return;
    }

    try {
      setSending(true);
      const response = await axios.post(API_ROUTES.sendReport, {
        month,
        year,
        recipient_ids: null // Null triggers sending to all active recipients
      });
      
      if (response.data.status === 'sent') {
        Alert.alert(
          'Report Dispatched!',
          `Successfully emailed expense report to:\n${response.data.recipients.join('\n')}`
        );
      } else {
        Alert.alert('Failed', response.data.error || 'Failed to send report.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'An error occurred while sending the email.';
      Alert.alert('Error', msg);
    } finally {
      setSending(false);
    }
  };

  // Load report data when month/year changes
  useEffect(() => {
    fetchReport(month, year);
  }, [month, year]);

  // Load active recipients when tab focuses
  useFocusEffect(
    useCallback(() => {
      fetchRecipients();
    }, [])
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContent} 
        keyboardShouldPersistTaps="handled"
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
          <Text style={styles.headerTitle}>Monthly Reports</Text>
          <Text style={styles.headerSubtitle}>Analyze and share statement summaries with parents</Text>
        </View>

        {/* Period Navigation Selector */}
        <View style={styles.periodCard}>
          <Pressable style={styles.arrowButton} onPress={handlePrevMonth}>
            <Ionicons name="chevron-back" size={20} color="#059669" />
          </Pressable>
          <View style={styles.periodTextContainer}>
            <Ionicons name="calendar" size={16} color="#059669" style={{ marginRight: 8 }} />
            <Text style={styles.periodLabel}>
              {monthsList[month - 1]} {year}
            </Text>
          </View>
          <Pressable style={styles.arrowButton} onPress={handleNextMonth}>
            <Ionicons name="chevron-forward" size={20} color="#059669" />
          </Pressable>
        </View>

        {/* Primary Content Loading & Render Status */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#059669" />
            <Text style={styles.loadingText}>Fetching statement data and compiling report...</Text>
          </View>
        ) : errorText ? (
          /* Empty / No Statement State */
          <View style={styles.emptyCard}>
            <View style={styles.emptyIconCircle}>
              <Ionicons name="document-outline" size={36} color="#94A3B8" />
            </View>
            <Text style={styles.emptyTitle}>No Reconciled Data Found</Text>
            <Text style={styles.emptyText}>
              There are no statements loaded or reconciled for {monthsList[month - 1]} {year}.
            </Text>
            <Pressable 
              style={styles.actionButton}
              onPress={() => router.push('/upload')}
            >
              <Ionicons name="cloud-upload-outline" size={18} color="#FFFFFF" style={{ marginRight: 8 }} />
              <Text style={styles.actionButtonText}>Upload Statement</Text>
            </Pressable>
          </View>
        ) : (
          /* Success / Report Loaded State */
          <View>
            {/* Metallic Dark Emerald Insights Card */}
            <View style={styles.insightsCard}>
              <View style={styles.insightsHeader}>
                <View style={styles.sparkleCircle}>
                  <Ionicons name="sparkles" size={16} color="#34D399" />
                </View>
                <Text style={styles.insightsTitle}>AI Parental Overview</Text>
              </View>
              
              <View style={styles.quoteWrapper}>
                <Text style={styles.quoteTextLeft}>“</Text>
                <Text style={styles.insightsBody}>{insights}</Text>
                <Text style={styles.quoteTextRight}>”</Text>
              </View>
            </View>

            {/* Actions Grid */}
            <View style={styles.actionGrid}>
              <Pressable style={[styles.gridButton, styles.downloadBtn]} onPress={handleDownload}>
                <Ionicons name="download-outline" size={18} color="#059669" style={{ marginRight: 8 }} />
                <Text style={styles.downloadBtnText}>Excel Report</Text>
              </Pressable>

              <Pressable 
                style={[styles.gridButton, styles.sendBtn, sending && styles.btnDisabled]} 
                onPress={handleSendEmail}
                disabled={sending}
              >
                {sending ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <Ionicons name="mail" size={18} color="#FFFFFF" style={{ marginRight: 8 }} />
                    <Text style={styles.sendBtnText}>Email Parents</Text>
                  </>
                )}
              </Pressable>
            </View>
          </View>
        )}

        {/* Recipients Manager Card */}
        <View style={styles.recipientsCard}>
          <View style={styles.recipientsHeader}>
            <View style={styles.recipientsHeaderIconCircle}>
              <Ionicons name="people" size={20} color="#059669" />
            </View>
            <Text style={styles.recipientsTitle}>Configure Recipients</Text>
          </View>
          <Text style={styles.recipientsDesc}>
            Add the names and emails of parents or guardians to receive dispatched report emails.
          </Text>

          {/* Add Recipient Form */}
          <View style={styles.formRow}>
            <TextInput 
              style={[styles.input, { flex: 1 }]}
              placeholder="Name"
              placeholderTextColor="#94A3B8"
              value={newRecipName}
              onChangeText={setNewRecipName}
            />
            <TextInput 
              style={[styles.input, { flex: 2 }]}
              placeholder="Parent Email"
              placeholderTextColor="#94A3B8"
              keyboardType="email-address"
              autoCapitalize="none"
              value={newRecipEmail}
              onChangeText={setNewRecipEmail}
            />
            <Pressable 
              style={[styles.addBtn, addingRecip && styles.btnDisabled]} 
              onPress={handleAddRecipient}
              disabled={addingRecip}
            >
              {addingRecip ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Ionicons name="add" size={22} color="#FFFFFF" />
              )}
            </Pressable>
          </View>

          {/* Recipients List */}
          <View style={styles.recipientsList}>
            {recipients.length === 0 ? (
              <View style={styles.emptyListContainer}>
                <Text style={styles.emptyListText}>No recipients added yet.</Text>
              </View>
            ) : (
              recipients.map((recip) => (
                <View key={recip.id} style={styles.recipItem}>
                  <View style={styles.avatarCircle}>
                    <Text style={styles.avatarText}>{getInitials(recip.name)}</Text>
                  </View>
                  <View style={styles.recipInfo}>
                    <Text style={styles.recipName}>{recip.name}</Text>
                    <Text style={styles.recipEmail}>{recip.email}</Text>
                  </View>
                  <Pressable 
                    style={styles.deleteBtn}
                    onPress={() => handleDeleteRecipient(recip.id)}
                  >
                    <Ionicons name="trash-outline" size={16} color="#EF4444" />
                  </Pressable>
                </View>
              ))
            )}
          </View>
        </View>
      </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFBFD',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 110,
  },
  header: {
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 6,
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '500',
    lineHeight: 18,
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
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  loadingText: {
    marginTop: 16,
    color: '#64748B',
    fontSize: 13,
    fontWeight: '500',
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  emptyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.02,
    shadowRadius: 12,
    elevation: 1,
    marginBottom: 24,
  },
  emptyIconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#F1F5F9',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 20,
    paddingHorizontal: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#059669',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 14,
    shadowColor: '#059669',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  insightsCard: {
    backgroundColor: '#073E28', // Dark Emerald card
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: '#0C5E3E',
    shadowColor: '#059669',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 6,
    marginBottom: 20,
  },
  insightsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sparkleCircle: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#047857',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  insightsTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ECFDF5',
  },
  quoteWrapper: {
    position: 'relative',
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  quoteTextLeft: {
    position: 'absolute',
    left: -4,
    top: -12,
    fontSize: 48,
    fontFamily: 'serif',
    color: '#047857',
    opacity: 0.25,
  },
  quoteTextRight: {
    position: 'absolute',
    right: -4,
    bottom: -28,
    fontSize: 48,
    fontFamily: 'serif',
    color: '#047857',
    opacity: 0.25,
  },
  insightsBody: {
    fontSize: 14,
    lineHeight: 22,
    color: '#ECFDF5',
    fontStyle: 'italic',
    fontWeight: '500',
    textAlign: 'center',
    paddingVertical: 8,
  },
  actionGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  gridButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 52,
    borderRadius: 16,
    borderWidth: 1,
  },
  downloadBtn: {
    backgroundColor: '#FFFFFF',
    borderColor: '#E2E8F0',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.02,
    shadowRadius: 8,
    elevation: 1,
  },
  downloadBtnText: {
    color: '#059669',
    fontSize: 14,
    fontWeight: '700',
  },
  sendBtn: {
    backgroundColor: '#059669',
    borderColor: '#059669',
    shadowColor: '#059669',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.18,
    shadowRadius: 12,
    elevation: 3,
  },
  sendBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  btnDisabled: {
    opacity: 0.6,
  },
  recipientsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.02,
    shadowRadius: 12,
    elevation: 1,
  },
  recipientsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 8,
  },
  recipientsHeaderIconCircle: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: '#ECFDF5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recipientsTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
  },
  recipientsDesc: {
    fontSize: 12.5,
    color: '#64748B',
    lineHeight: 18,
    marginBottom: 18,
  },
  formRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#F1F5F9', // Pill inputs
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 13.5,
    color: '#0F172A',
    borderWidth: 0,
  },
  addBtn: {
    backgroundColor: '#059669',
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#059669',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 2,
  },
  recipientsList: {
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: 12,
  },
  emptyListContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  emptyListText: {
    color: '#94A3B8',
    fontSize: 13,
    fontStyle: 'italic',
  },
  recipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F8FAFC',
  },
  avatarCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#ECFDF5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 1.5,
    borderColor: '#D1FAE5',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#065F46',
  },
  recipInfo: {
    flex: 1,
  },
  recipName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0F172A',
    marginBottom: 2,
  },
  recipEmail: {
    fontSize: 12,
    color: '#64748B',
  },
  deleteBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FEF2F2',
    justifyContent: 'center',
    alignItems: 'center',
  },
});