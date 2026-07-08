import { View, Text, Button, ActivityIndicator } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { useState } from 'react';
import axios from 'axios';

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
            setStatus('Uploading...');

            // Back to the original, clean React Native object hack
            const formData = new FormData();
            formData.append('file', {
                uri: asset.uri,
                name: asset.name ?? 'statement.pdf',
                type: asset.mimeType ?? 'application/pdf',
            } as any);

            // Execute using Axios to bypass the fetch API completely
            const response = await axios.post(
                'http://192.168.88.8:8000/api/upload-statement',
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

    return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16 }}>
            <Button title="Upload GPay Statement" onPress={pick_doc} />
            {loading && <ActivityIndicator size="large" />}
            {status !== '' && (
                <Text style={{ textAlign: 'center', paddingHorizontal: 24 }}>
                    {status}
                </Text>
            )}
        </View>
    );
}