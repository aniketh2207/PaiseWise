// components/AnnotateModal.tsx
import { Modal, View, Text, TextInput, Pressable, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { useState, useEffect } from 'react';
import { Ionicons } from '@expo/vector-icons';

const CATEGORIES = ['Food', 'Travel', 'Shopping', 'Utilities', 'Entertainment', 'Education', 'Health', 'Transfer', 'Other'];

interface Props {
    visible: boolean;
    transaction: any;
    onClose: () => void;
    onSave: (id: number, category: string, subcategory: string, reason: string, remember: boolean) => void;
}

export default function AnnotateModal({ visible, transaction, onClose, onSave }: Props) {
    const [category, setCategory] = useState('');
    const [subcategory, setSubcategory] = useState('');
    const [reason, setReason] = useState('');
    const [remember, setRemember] = useState(true);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

    // Reset local inputs when modal opens or transaction changes
    useEffect(() => {
        if (transaction) {
            setCategory(transaction.category || '');
            setSubcategory(transaction.subcategory || '');
            setReason(transaction.reason || '');
            setRemember(true);
        }
    }, [transaction, visible]);

    if (!transaction) return null;

    const handleSave = () => {
        onSave(transaction.id, category, subcategory, reason, remember);
        onClose();
    };

    const filteredCategories = CATEGORIES.filter((c) =>
        c.toLowerCase().includes(category.toLowerCase())
    );

    return (
        <Modal visible={visible} animationType="slide" transparent>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={styles.overlay}
            >
                <View style={styles.sheet}>
                    {/* Drag Handle indicator */}
                    <View style={styles.dragHandle} />

                    <ScrollView 
                        contentContainerStyle={styles.scrollContainer} 
                        keyboardShouldPersistTaps="handled"
                        showsVerticalScrollIndicator={false}
                    >
                        {/* Transaction Header Info */}
                        <View style={styles.headerInfo}>
                            <Text style={styles.title}>{transaction.upi_name || transaction.raw_description}</Text>
                            <Text style={[
                                styles.amount, 
                                { color: transaction.type === 'credit' ? '#10B981' : '#0F172A' }
                            ]}>
                                {transaction.type === 'credit' ? '+' : '-'}₹{Math.abs(transaction.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </Text>
                        </View>

                        {/* Category Input & Search Dropdown */}
                        <Text style={styles.label}>Category</Text>
                        <View style={styles.inputContainer}>
                            <Ionicons name="search" size={18} color="#94A3B8" style={styles.inputIcon} />
                            <TextInput
                                style={styles.input}
                                value={category}
                                onChangeText={(text) => {
                                    setCategory(text);
                                    setIsDropdownOpen(true);
                                }}
                                onFocus={() => setIsDropdownOpen(true)}
                                onBlur={() => {
                                    // Slight delay to allow item selection press to register
                                    setTimeout(() => setIsDropdownOpen(false), 200);
                                }}
                                placeholder="Search or enter category..."
                                autoCorrect={false}
                                autoCapitalize="none"
                            />
                        </View>

                        {isDropdownOpen && (
                            <View style={styles.dropdown}>
                                <ScrollView nestedScrollEnabled style={styles.dropdownScroll} keyboardShouldPersistTaps="handled">
                                    {filteredCategories.map((c) => (
                                        <Pressable
                                            key={c}
                                            onPress={() => {
                                                setCategory(c);
                                                setIsDropdownOpen(false);
                                            }}
                                            style={styles.dropdownItem}
                                        >
                                            <Text style={styles.dropdownItemText}>{c}</Text>
                                        </Pressable>
                                    ))}
                                    {filteredCategories.length === 0 && category.trim() !== '' && (
                                        <View style={styles.dropdownItem}>
                                            <Text style={styles.dropdownItemTextLight}>Create new: "{category}"</Text>
                                        </View>
                                    )}
                                </ScrollView>
                            </View>
                        )}

                        {/* Subcategory Input */}
                        <Text style={styles.label}>Subcategory</Text>
                        <View style={styles.inputContainer}>
                            <Ionicons name="pricetag-outline" size={18} color="#94A3B8" style={styles.inputIcon} />
                            <TextInput
                                style={styles.input}
                                value={subcategory}
                                onChangeText={setSubcategory}
                                placeholder="e.g. Grocery, Auto/Cab, Rent"
                            />
                        </View>

                        {/* Reason Input */}
                        <Text style={styles.label}>Reason / Purpose</Text>
                        <View style={styles.inputContainer}>
                            <Ionicons name="chatbubble-ellipses-outline" size={18} color="#94A3B8" style={styles.inputIcon} />
                            <TextInput
                                style={styles.input}
                                value={reason}
                                onChangeText={setReason}
                                placeholder="Why did you spend this?"
                            />
                        </View>

                        {/* Remember UPI Checkbox Toggle */}
                        <Pressable 
                            onPress={() => setRemember(!remember)} 
                            style={styles.rememberRow}
                        >
                            <Ionicons 
                                name={remember ? 'checkbox' : 'square-outline'} 
                                size={22} 
                                color={remember ? '#059669' : '#64748B'} 
                                style={{ marginRight: 8 }} 
                            />
                            <Text style={styles.rememberText}>Remember category for this UPI merchant</Text>
                        </Pressable>

                        {/* Modal Action Buttons */}
                        <View style={styles.buttonRow}>
                            <Pressable onPress={onClose} style={styles.cancelBtn}>
                                <Text style={styles.cancelBtnText}>Cancel</Text>
                            </Pressable>
                            
                            <Pressable 
                                onPress={handleSave} 
                                style={({ pressed }) => [
                                    styles.saveBtn,
                                    pressed && styles.saveBtnPressed,
                                    (!category.trim()) && styles.saveBtnDisabled
                                ]}
                                disabled={!category.trim()}
                            >
                                <Text style={styles.saveBtnText}>Save Annotation</Text>
                            </Pressable>
                        </View>
                    </ScrollView>
                </View>
            </KeyboardAvoidingView>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: { 
        flex: 1, 
        backgroundColor: 'rgba(15, 23, 42, 0.5)', // Slate dark semi-transparent dim
        justifyContent: 'flex-end' 
    },
    sheet: { 
        backgroundColor: '#FFFFFF', 
        borderTopLeftRadius: 28, 
        borderTopRightRadius: 28, 
        paddingHorizontal: 24,
        paddingBottom: 24,
        maxHeight: '85%' 
    },
    dragHandle: {
        width: 38,
        height: 4,
        borderRadius: 2,
        backgroundColor: '#E2E8F0',
        alignSelf: 'center',
        marginTop: 12,
        marginBottom: 16,
    },
    scrollContainer: {
        paddingBottom: 32,
    },
    headerInfo: {
        alignItems: 'center',
        marginBottom: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#F1F5F9',
        paddingBottom: 20,
    },
    title: { 
        fontSize: 18, 
        fontWeight: '700',
        color: '#0F172A',
        textAlign: 'center',
        marginBottom: 6,
    },
    amount: { 
        fontSize: 26, 
        fontWeight: '800', 
    },
    label: { 
        fontSize: 13, 
        color: '#475569', 
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        marginTop: 16, 
        marginBottom: 6 
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        borderWidth: 1, 
        borderColor: '#E2E8F0', 
        borderRadius: 14, 
        backgroundColor: '#F8FAFC',
        paddingHorizontal: 14,
    },
    inputIcon: {
        marginRight: 10,
    },
    input: { 
        flex: 1,
        height: 48,
        fontSize: 14,
        color: '#0F172A',
        fontWeight: '500',
    },
    dropdown: {
        borderWidth: 1,
        borderColor: '#E2E8F0',
        borderRadius: 14,
        backgroundColor: '#FFFFFF',
        maxHeight: 160,
        marginTop: 6,
        zIndex: 1000,
        // premium soft shadow
        shadowColor: '#0F172A',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
        elevation: 4,
    },
    dropdownScroll: {
        maxHeight: 160,
    },
    dropdownItem: {
        paddingHorizontal: 14,
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#F8FAFC',
    },
    dropdownItemText: {
        fontSize: 14,
        color: '#1E293B',
        fontWeight: '500',
    },
    dropdownItemTextLight: {
        fontSize: 14,
        color: '#94A3B8',
        fontStyle: 'italic',
    },
    rememberRow: { 
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 20,
        paddingVertical: 4,
    },
    rememberText: {
        fontSize: 13,
        fontWeight: '500',
        color: '#334155',
    },
    buttonRow: { 
        flexDirection: 'row', 
        justifyContent: 'flex-end', 
        alignItems: 'center',
        gap: 16, 
        marginTop: 28 
    },
    cancelBtn: { 
        paddingVertical: 14,
        paddingHorizontal: 20,
    },
    cancelBtnText: {
        color: '#64748B',
        fontSize: 15,
        fontWeight: '600',
    },
    saveBtn: { 
        backgroundColor: '#059669', 
        paddingHorizontal: 24, 
        paddingVertical: 14, 
        borderRadius: 14,
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        flex: 1,
        // shadow
        shadowColor: '#059669',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
        elevation: 3,
    },
    saveBtnPressed: {
        backgroundColor: '#047857',
        opacity: 0.9,
    },
    saveBtnDisabled: {
        backgroundColor: '#E2E8F0',
        shadowOpacity: 0,
        elevation: 0,
    },
    saveBtnText: { 
        color: '#FFFFFF',
        fontSize: 15,
        fontWeight: '600',
    },
});