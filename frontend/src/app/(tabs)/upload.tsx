import { View, Text, StyleSheet, Pressable, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as DocumentPicker from 'expo-document-picker';
import { useState } from 'react';
import axios from 'axios';
import { API_ROUTES } from '../../constants/api';

export default function Upload() {
    const [status, setStatus] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);

    const pick_doc = async () => {
        const res = await DocumentPicker.getDocumentAsync({
            type: 'application/pdf',
            copyToCacheDirectory: true,
            multiple: false,
        });

        if (res.canceled) return;
        const asset = res.assets[0];

        try {
            setLoading(true);
            setStatus('Uploading statement...');

            // Back to the original, clean React Native object hack
            const formData = new FormData();
            formData.append('file', {
                uri: asset.uri,
                name: asset.name ?? 'statement.pdf',
                type: asset.mimeType ?? 'application/pdf',
            } as any);

            // Execute using Axios to bypass the fetch API completely
            const response = await axios.post(
                API_ROUTES.uploadStatement,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                }
            );

            // Axios automatically parses JSON, so response.data holds your backend reply
            const result = response.data;
            if (result.status === 'success') {
                setStatus(`✅ Success: ${result.total_transactions} transactions found.`);
            } else if (result.status === 'warning') {
                setStatus(`⚠️ Warning: ${result.message}`);
            } else {
                setStatus(`✅ Uploaded successfully.`);
            }
            console.log('Upload successful', response.data);

        } catch (error: any) {
            // Axios conveniently nests backend error messages inside error.response.data
            const errMsg = error.response?.data?.detail || error.message;
            setStatus(`❌ Error: ${errMsg}`);
            console.log('Upload error', error);
        } finally {
            setLoading(false);
        }
    };

    const renderStatus = () => {
        if (!status) return null;
        
        const isSuccess = status.includes('✅') || status.toLowerCase().includes('success');
        const isWarning = status.includes('⚠️') || status.toLowerCase().includes('warning');
        const isError = status.includes('❌') || status.toLowerCase().includes('error');
        
        const cleanStatusText = status.replace(/[✅⚠️❌]/g, '').trim();

        return (
            <View style={[
                styles.statusBanner,
                isSuccess && styles.statusSuccess,
                isWarning && styles.statusWarning,
                isError && styles.statusError,
            ]}>
                <Ionicons 
                    name={isSuccess ? "checkmark-circle" : isWarning ? "alert-circle" : "close-circle"} 
                    size={20} 
                    color={isSuccess ? "#10B981" : isWarning ? "#F59E0B" : "#EF4444"} 
                />
                <Text style={[
                    styles.statusText,
                    isSuccess && styles.textSuccess,
                    isWarning && styles.textWarning,
                    isError && styles.textError,
                ]}>
                    {cleanStatusText}
                </Text>
            </View>
        );
    };

    return (
        <SafeAreaView style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Import Statement</Text>
                <Text style={styles.headerSubtitle}>Import your Google Pay PDF statements here</Text>
            </View>

            {/* Upload Area */}
            <View style={styles.uploadCard}>
                <View style={styles.iconCircle}>
                    <Ionicons name="document-text" size={44} color="#6366F1" />
                </View>
                <Text style={styles.uploadTitle}>Upload PDF Statement</Text>
                <Text style={styles.uploadDesc}>Select a Google Pay exported PDF statement file from your device.</Text>

                <Pressable 
                    onPress={pick_doc} 
                    disabled={loading}
                    style={({ pressed }) => [
                        styles.uploadBtn,
                        pressed && styles.uploadBtnPressed,
                        loading && styles.uploadBtnDisabled
                    ]}
                >
                    <Ionicons name="cloud-upload-outline" size={20} color="#FFFFFF" style={{ marginRight: 8 }} />
                    <Text style={styles.uploadBtnText}>Select File</Text>
                </Pressable>
            </View>

            {/* Status Section */}
            <View style={styles.statusContainer}>
                {loading && (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#5F33E1" />
                        <Text style={styles.loadingText}>Reading PDF and extracting transactions...</Text>
                    </View>
                )}
                {!loading && renderStatus()}
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F8FAFC',
        paddingHorizontal: 24,
        paddingTop: 16,
    },
    header: {
        marginBottom: 32,
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
    uploadCard: {
        backgroundColor: '#FFFFFF',
        borderRadius: 24,
        padding: 32,
        alignItems: 'center',
        borderWidth: 2,
        borderColor: '#E2E8F0',
        borderStyle: 'dashed',
        // soft shadow
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.03,
        shadowRadius: 10,
        elevation: 2,
        marginBottom: 24,
    },
    iconCircle: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: '#EEF2FF',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 20,
    },
    uploadTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#0F172A',
        marginBottom: 8,
    },
    uploadDesc: {
        fontSize: 13,
        color: '#64748B',
        textAlign: 'center',
        lineHeight: 20,
        marginBottom: 28,
        paddingHorizontal: 12,
    },
    uploadBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#5F33E1',
        paddingHorizontal: 28,
        paddingVertical: 14,
        borderRadius: 14,
        width: '100%',
    },
    uploadBtnPressed: {
        backgroundColor: '#4B25B3',
        opacity: 0.9,
    },
    uploadBtnDisabled: {
        backgroundColor: '#94A3B8',
    },
    uploadBtnText: {
        color: '#FFFFFF',
        fontSize: 15,
        fontWeight: '600',
    },
    statusContainer: {
        marginTop: 8,
    },
    loadingContainer: {
        alignItems: 'center',
        padding: 16,
    },
    loadingText: {
        marginTop: 12,
        color: '#475569',
        fontSize: 14,
        textAlign: 'center',
    },
    statusBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
        borderRadius: 16,
        borderWidth: 1,
        gap: 12,
    },
    statusSuccess: {
        backgroundColor: '#ECFDF5',
        borderColor: '#A7F3D0',
    },
    statusWarning: {
        backgroundColor: '#FFFBEB',
        borderColor: '#FDE68A',
    },
    statusError: {
        backgroundColor: '#FEF2F2',
        borderColor: '#FEE2E2',
    },
    statusText: {
        fontSize: 14,
        fontWeight: '500',
        flex: 1,
    },
    textSuccess: {
        color: '#065F46',
    },
    textWarning: {
        color: '#92400E',
    },
    textError: {
        color: '#991B1B',
    },
});