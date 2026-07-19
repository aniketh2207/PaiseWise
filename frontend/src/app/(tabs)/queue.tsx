import { View, Text, ActivityIndicator, FlatList, StyleSheet, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useState, useCallback } from 'react';
import { useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { API_ROUTES } from '../../constants/api';
import AnnotateModal from '../../components/Annotation_queue';
import { dashboardCache } from '../../utils/dashboardCache';

// Define the blueprint for your transaction
interface Transaction {
    id?: number;
    amount: number;
    reason: string;
    category: string;
    subcategory: string;
    notes: string;
    type: string;
    date: string;
    time: string;
    raw_description: string;
    reconcile_status: string;
    needs_annotation: boolean;
    month: number;
    year: number;
}

export default function Queue() {
    const [transactions, set_transactions] = useState<Transaction[]>([]);
    const [loading, set_loading] = useState<boolean>(true);
    const [error, set_error] = useState<string>('');

    const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);
    const [modalVisible, setModalVisible] = useState(false);
    
    const fetch_queue = async () => {
        try {
            set_loading(true);
            const response = await axios.get(API_ROUTES.annotationQueue);
            set_transactions(response.data.data);
            set_error('');
        } catch (error) {
            set_error('Failed to fetch queue items');
            console.log(error);
        } finally {
            set_loading(false);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetch_queue();
        }, [])
    );

    const handleSaveAnnotation = async (
        id: number, category: string, subcategory: string, reason: string, remember: boolean
    ) => {
        try {
            await axios.patch(API_ROUTES.annotateTransaction(id), {
                category, subcategory, reason, remember_upi: remember,
            });
            // remove from local list immediately (optimistic update)
            set_transactions(prev => prev.filter(t => t.id !== id));
            dashboardCache.invalidate();
        } catch (error) {
            console.log('Annotation failed', error);
        }
    };

    const render_item = ({ item }: { item: Transaction }) => {
        const isCredit = item.type === 'credit';
        return (
            <Pressable 
                onPress={() => { setSelectedTxn(item); setModalVisible(true); }}
                style={({ pressed }) => [
                    styles.cardWrapper,
                    pressed && styles.cardPressed
                ]}
            >
                <View style={[styles.card, { borderLeftColor: isCredit ? '#10B981' : '#EF4444' }]}>
                    <View style={styles.cardHeader}>
                        <View style={styles.dateContainer}>
                            <Ionicons name="calendar-outline" size={14} color="#64748B" style={{ marginRight: 4 }} />
                            <Text style={styles.date}>{item.date} {item.time ? `• ${item.time}` : ''}</Text>
                        </View>
                        <Text style={[styles.amount, { color: isCredit ? '#10B981' : '#EF4444' }]}>
                            {isCredit ? '+' : '-'}₹{Math.abs(item.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </Text>
                    </View>
                    
                    <Text style={styles.description} numberOfLines={2}>{item.raw_description}</Text>
                    
                    <View style={styles.badgeRow}>
                        <View style={styles.categoryBadge}>
                            <Ionicons name="pricetag-outline" size={12} color="#475569" style={{ marginRight: 4 }} />
                            <Text style={styles.categoryText}>{item.category || 'Uncategorized'}</Text>
                        </View>
                        
                        <View style={[
                            styles.typeBadge,
                            {
                                backgroundColor: isCredit ? '#E6FFFA' : '#FFEFEB',
                            }
                        ]}>
                            <Text style={[
                                styles.typeBadgeText,
                                {
                                    color: isCredit ? '#0D9488' : '#E11D48'
                                }
                            ]}>
                                {isCredit ? 'INCOME' : 'EXPENSE'}
                            </Text>
                        </View>
                    </View>
                </View>
            </Pressable>
        );
    };

    return (
        <SafeAreaView style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Action Queue</Text>
                <Text style={styles.headerSubtitle}>Tap on any transaction below to annotate it</Text>
            </View>

            {loading ? (
                <View style={styles.centerContainer}>
                    <ActivityIndicator size="large" color="#059669" />
                    <Text style={styles.loadingText}>Fetching pending items...</Text>
                </View>
            ) : error !== '' ? (
                <View style={styles.centerContainer}>
                    <Ionicons name="alert-circle-outline" size={48} color="#EF4444" />
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            ) : transactions.length === 0 ? (
                <View style={styles.centerContainer}>
                    <View style={styles.emptyCircle}>
                        <Ionicons name="checkmark-done" size={48} color="#10B981" />
                    </View>
                    <Text style={styles.emptyTextTitle}>All Caught Up!</Text>
                    <Text style={styles.emptyTextSub}>No transactions need annotation right now.</Text>
                </View>
            ) : (
                <FlatList
                    data={transactions}
                    keyExtractor={(item, index) => item.id?.toString() || index.toString()}
                    renderItem={render_item}
                    contentContainerStyle={styles.listContent}
                    showsVerticalScrollIndicator={false}
                />
            )}
            
            <AnnotateModal
                visible={modalVisible}
                transaction={selectedTxn}
                onClose={() => setModalVisible(false)}
                onSave={handleSaveAnnotation}
            />
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F8FAFC',
        paddingHorizontal: 20,
        paddingTop: 16,
    },
    header: {
        marginBottom: 24,
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#0F172A',
        marginBottom: 6,
    },
    headerSubtitle: {
        fontSize: 14,
        color: '#64748B',
        fontWeight: '500',
    },
    listContent: {
        paddingBottom: 110,
    },
    cardWrapper: {
        marginBottom: 14,
    },
    cardPressed: {
        opacity: 0.9,
        transform: [{ scale: 0.99 }],
    },
    card: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        padding: 18,
        borderLeftWidth: 5,
        borderWidth: 1,
        borderColor: '#F1F5F9',
        // premium shadow
        shadowColor: '#0F172A',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.03,
        shadowRadius: 8,
        elevation: 2,
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 10,
    },
    dateContainer: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    date: {
        fontSize: 12,
        color: '#64748B',
        fontWeight: '600',
    },
    amount: {
        fontSize: 18,
        fontWeight: '700',
    },
    description: {
        fontSize: 15,
        fontWeight: '600',
        color: '#1E293B',
        lineHeight: 22,
        marginBottom: 14,
    },
    badgeRow: {
        flexDirection: 'row',
        gap: 8,
        alignItems: 'center',
    },
    categoryBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        alignSelf: 'flex-start',
        backgroundColor: '#F1F5F9',
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 10,
    },
    categoryText: {
        color: '#475569',
        fontSize: 12,
        fontWeight: '600',
    },
    typeBadge: {
        alignSelf: 'flex-start',
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 10,
    },
    typeBadgeText: {
        fontSize: 10,
        fontWeight: '700',
        letterSpacing: 0.5,
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingBottom: 80,
    },
    loadingText: {
        marginTop: 12,
        color: '#64748B',
        fontSize: 14,
    },
    errorText: {
        color: '#EF4444',
        textAlign: 'center',
        marginTop: 12,
        fontSize: 15,
        fontWeight: '500',
    },
    emptyCircle: {
        width: 88,
        height: 88,
        borderRadius: 44,
        backgroundColor: '#ECFDF5',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 20,
    },
    emptyTextTitle: {
        fontSize: 20,
        fontWeight: '700',
        color: '#0F172A',
        marginBottom: 6,
    },
    emptyTextSub: {
        textAlign: 'center',
        color: '#64748B',
        fontSize: 14,
        paddingHorizontal: 32,
    },
});