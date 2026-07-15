import React, { useState, useCallback, useEffect } from 'react';
import { View, StyleSheet, Text, Platform, KeyboardAvoidingView, Keyboard, TouchableOpacity, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GiftedChat, Bubble, Send, InputToolbar, Composer, IMessage } from 'react-native-gifted-chat';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import * as FileSystem from 'expo-file-system/legacy';
import { API_ROUTES } from '../../constants/api';

const CHAT_HISTORY_FILE = `${FileSystem.documentDirectory}chat_history.json`;

export default function ChatScreen() {
  const [messages, setMessages] = useState<IMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isKeyboardVisible, setKeyboardVisible] = useState(false);
  const insets = useSafeAreaInsets();

  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const showSub = Keyboard.addListener(showEvent, () => setKeyboardVisible(true));
    const hideSub = Keyboard.addListener(hideEvent, () => setKeyboardVisible(false));

    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, []);

  // Load chat history from FileSystem on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const fileInfo = await FileSystem.getInfoAsync(CHAT_HISTORY_FILE);
        if (fileInfo.exists) {
          const content = await FileSystem.readAsStringAsync(CHAT_HISTORY_FILE);
          const parsed = JSON.parse(content);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setMessages(parsed);
            return;
          }
        }
      } catch (err) {
        console.log('Error loading chat history:', err);
      }
      // Fallback if no history exists yet
      setMessages([
        {
          _id: 1,
          text: 'Log an expense or ask about your spending',
          createdAt: new Date().getTime(),
          user: {
            _id: 2,
            name: 'PaiseWise Bot',
          },
        },
      ]);
    };
    loadHistory();
  }, []);

  // Save chat history automatically whenever messages are updated
  useEffect(() => {
    if (messages.length > 0) {
      FileSystem.writeAsStringAsync(CHAT_HISTORY_FILE, JSON.stringify(messages))
        .catch(err => console.log('Error saving chat history:', err));
    }
  }, [messages]);

  const clearChatHistory = useCallback(() => {
    Alert.alert(
      'Clear Chat',
      'Are you sure you want to clear your chat history?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              const fileInfo = await FileSystem.getInfoAsync(CHAT_HISTORY_FILE);
              if (fileInfo.exists) {
                await FileSystem.deleteAsync(CHAT_HISTORY_FILE);
              }
              setMessages([
                {
                  _id: 1,
                  text: 'Log an expense or ask about your spending',
                  createdAt: new Date().getTime(),
                  user: {
                    _id: 2,
                    name: 'PaiseWise Bot',
                  },
                },
              ]);
            } catch (err) {
              console.log('Error clearing chat history:', err);
            }
          },
        },
      ]
    );
  }, []);

  const onSend = useCallback(async (newMessages: IMessage[] = []) => {
    const userMessage = newMessages[0];
    if (!userMessage || !userMessage.text.trim()) return;

    // Get the last 5 messages from the current conversation in chronological order
    const historyPayload = messages.slice(0, 5).reverse().map(m => ({
      role: m.user._id === 1 ? 'user' : 'assistant',
      content: m.text,
    }));

    setMessages(previousMessages =>
      GiftedChat.append(previousMessages, newMessages)
    );

    setIsTyping(true);

    try {
      const response = await axios.post(API_ROUTES.chat, {
        message: userMessage.text,
        history: historyPayload,
      });

      const replyText = response.data?.reply || 'Logged successfully.';
      const botMessage: IMessage = {
        _id: `bot_${new Date().getTime()}`,
        text: replyText,
        createdAt: new Date().getTime(),
        user: {
          _id: 2,
          name: 'PaiseWise Bot',
        },
      };

      setMessages(previousMessages =>
        GiftedChat.append(previousMessages, [botMessage])
      );
    } catch (err) {
      console.log('Chat API Error:', err);
      const errorMessage: IMessage = {
        _id: `error_${new Date().getTime()}`,
        text: 'Sorry, I ran into an error connecting to the backend. Please check your network and try again.',
        createdAt: new Date().getTime(),
        user: {
          _id: 2,
          name: 'PaiseWise Bot',
        },
      };
      setMessages(previousMessages =>
        GiftedChat.append(previousMessages, [errorMessage])
      );
    } finally {
      setIsTyping(false);
    }
  }, [messages]);

  const renderBubble = useCallback((props: any) => {
    return (
      <Bubble
        {...props}
        wrapperStyle={{
          right: {
            backgroundColor: '#5F33E1',
            borderRadius: 16,
            padding: 4,
            shadowColor: '#5F33E1',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.15,
            shadowRadius: 6,
            elevation: 3,
          },
          left: {
            backgroundColor: '#FFFFFF',
            borderRadius: 16,
            padding: 4,
            borderWidth: 1,
            borderColor: '#F1F5F9',
            shadowColor: '#0F172A',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.03,
            shadowRadius: 10,
            elevation: 1,
          },
        }}
        textStyle={{
          right: {
            color: '#FFFFFF',
            fontSize: 14,
            fontWeight: '500',
            lineHeight: 20,
          },
          left: {
            color: '#0F172A',
            fontSize: 14,
            fontWeight: '500',
            lineHeight: 20,
          },
        }}
      />
    );
  }, []);

  const renderInputToolbar = useCallback((props: any) => {
    return (
      <InputToolbar
        {...props}
        containerStyle={styles.inputToolbarContainer}
        primaryState={props.primaryState}
      />
    );
  }, []);

  const renderComposer = useCallback((props: any) => {
    return (
      <Composer
        {...props}
        textInputStyle={styles.textInput}
        placeholder="Ask a question or log an expense..."
        placeholderTextColor="#64748B"
      />
    );
  }, []);

  const renderSend = useCallback((props: any) => {
    return (
      <Send {...props} containerStyle={styles.sendContainer}>
        <View style={styles.sendButton}>
          <Ionicons name="send" size={16} color="#FFFFFF" />
        </View>
      </Send>
    );
  }, []);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.headerIconContainer}>
            <Ionicons name="chatbubbles" size={20} color="#5F33E1" />
          </View>
          <Text style={styles.headerTitle}>paiseWise Assistant</Text>
        </View>
        <TouchableOpacity style={styles.clearButton} onPress={clearChatHistory} activeOpacity={0.7}>
          <Ionicons name="trash-outline" size={20} color="#64748B" />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1, paddingBottom: isKeyboardVisible ? 0 : 100 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <GiftedChat
          messages={messages}
          onSend={onSend}
          user={{
            _id: 1,
            name: 'You',
          }}
          isTyping={isTyping}
          renderBubble={renderBubble}
          renderInputToolbar={renderInputToolbar}
          renderComposer={renderComposer}
          renderSend={renderSend}
          {...{ bottomOffset: Platform.OS === 'ios' ? insets.bottom : 0, keyboardShouldPersistTaps: 'handled' }}
        />
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: '#EEF2F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F172A',
  },
  clearButton: {
    padding: 6,
  },
  inputToolbarContainer: {
    backgroundColor: '#FFFFFF',
    borderTopWidth: 0,
    marginHorizontal: 16,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 8,
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '500',
    lineHeight: 18,
    marginTop: 0,
    marginBottom: 0,
  },
  sendContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    marginLeft: 8,
    marginRight: 4,
  },
  sendButton: {
    backgroundColor: '#5F33E1', 
    width: 36,
    height: 36,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#5F33E1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
});