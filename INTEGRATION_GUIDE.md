# Integration Guide - Medical AI Engine with OKSmed

Complete guide for integrating the Medical AI Engine with the OKSmed React Native application.

## Architecture

```
OKSmed App (React Native/Expo)
        ↓
Medical AI Engine API (FastAPI)
        ↓
DeepSeek + OCR
        ↓
SQLite Database
```

## Setup

### 1. Start the Medical AI Engine Server

```bash
cd /home/ubuntu/medical-ai-engine
python main.py server --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 2. Configure OKSmed App

Update the API endpoint in your React Native app:

```typescript
// In app/ai-reader.tsx or your API config
const AI_ENGINE_API = "http://your-server-ip:8000";
```

## API Integration Examples

### Upload PDF and Extract Questions

```typescript
import * as DocumentPicker from "expo-document-picker";

async function uploadPDF() {
  const result = await DocumentPicker.getDocumentAsync({
    type: "application/pdf",
  });

  if (!result.canceled) {
    const file = result.assets[0];
    
    const formData = new FormData();
    formData.append("file", {
      uri: file.uri,
      type: "application/pdf",
      name: file.name,
    });

    try {
      const response = await fetch(`${AI_ENGINE_API}/extract/pdf`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      console.log(`Extracted ${data.total_extracted} questions`);
      
      // Save questions to app database
      for (const question of data.questions) {
        await addQuestion(question);
      }
    } catch (error) {
      console.error("Error uploading PDF:", error);
    }
  }
}
```

### Upload Image and Extract Questions

```typescript
import * as ImagePicker from "expo-image-picker";

async function uploadImage() {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ImagePicker.MediaTypeOptions.Images,
  });

  if (!result.canceled) {
    const file = result.assets[0];
    
    const formData = new FormData();
    formData.append("file", {
      uri: file.uri,
      type: "image/jpeg",
      name: file.uri.split("/").pop(),
    });

    try {
      const response = await fetch(`${AI_ENGINE_API}/extract/image`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      console.log(`Extracted ${data.total_extracted} questions`);
      
      // Save questions
      for (const question of data.questions) {
        await addQuestion(question);
      }
    } catch (error) {
      console.error("Error uploading image:", error);
    }
  }
}
```

### Extract from Text

```typescript
async function extractFromText(text: string) {
  try {
    const response = await fetch(`${AI_ENGINE_API}/extract/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();
    console.log(`Extracted ${data.total_extracted} questions`);
    
    // Save questions
    for (const question of data.questions) {
      await addQuestion(question);
    }
  } catch (error) {
    console.error("Error extracting from text:", error);
  }
}
```

### Get Questions with Filters

```typescript
async function getQuestions(filters = {}) {
  const params = new URLSearchParams();
  
  if (filters.subject) params.append("subject", filters.subject);
  if (filters.lesson) params.append("lesson", filters.lesson);
  if (filters.high_yield) params.append("high_yield", "true");
  if (filters.difficulty) params.append("difficulty", filters.difficulty);
  
  try {
    const response = await fetch(
      `${AI_ENGINE_API}/questions?${params.toString()}`
    );
    const questions = await response.json();
    return questions;
  } catch (error) {
    console.error("Error fetching questions:", error);
    return [];
  }
}
```

### Record User Progress

```typescript
async function recordProgress(
  userId: string,
  questionId: number,
  isCorrect: boolean,
  timeSpent: number
) {
  try {
    const response = await fetch(`${AI_ENGINE_API}/progress`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        question_id: questionId,
        is_correct: isCorrect,
        time_spent_seconds: timeSpent,
      }),
    });

    const data = await response.json();
    console.log("Progress recorded:", data);
  } catch (error) {
    console.error("Error recording progress:", error);
  }
}
```

### Get Statistics

```typescript
async function getStatistics(userId?: string) {
  try {
    const url = userId
      ? `${AI_ENGINE_API}/statistics?user_id=${userId}`
      : `${AI_ENGINE_API}/statistics`;
    
    const response = await fetch(url);
    const stats = await response.json();
    return stats;
  } catch (error) {
    console.error("Error fetching statistics:", error);
    return null;
  }
}
```

## Updated AI Reader Component

Here's how to integrate with the AI Reader screen:

```typescript
import { useState } from "react";
import { ScrollView, Text, View, Pressable, Alert, ActivityIndicator } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import * as ImagePicker from "expo-image-picker";

const AI_ENGINE_API = "http://your-server-ip:8000";

export default function AIReaderScreen() {
  const [isLoading, setIsLoading] = useState(false);
  const [questions, setQuestions] = useState([]);

  const handleUploadPDF = async () => {
    try {
      setIsLoading(true);
      const result = await DocumentPicker.getDocumentAsync({
        type: "application/pdf",
      });

      if (!result.canceled) {
        const file = result.assets[0];
        const formData = new FormData();
        formData.append("file", {
          uri: file.uri,
          type: "application/pdf",
          name: file.name,
        });

        const response = await fetch(`${AI_ENGINE_API}/extract/pdf`, {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        setQuestions(data.questions);
        Alert.alert("Success", `Extracted ${data.total_extracted} questions`);
      }
    } catch (error) {
      Alert.alert("Error", error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadImage = async () => {
    try {
      setIsLoading(true);
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
      });

      if (!result.canceled) {
        const file = result.assets[0];
        const formData = new FormData();
        formData.append("file", {
          uri: file.uri,
          type: "image/jpeg",
          name: file.uri.split("/").pop(),
        });

        const response = await fetch(`${AI_ENGINE_API}/extract/image`, {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        setQuestions(data.questions);
        Alert.alert("Success", `Extracted ${data.total_extracted} questions`);
      }
    } catch (error) {
      Alert.alert("Error", error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView className="flex-1 p-4 bg-background">
      <Text className="text-3xl font-bold text-foreground mb-4">
        AI Reader
      </Text>

      <View className="gap-4">
        <Pressable
          onPress={handleUploadPDF}
          disabled={isLoading}
          className="bg-blue-600 p-4 rounded-lg"
        >
          {isLoading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text className="text-white font-bold text-center">
              📄 Upload PDF
            </Text>
          )}
        </Pressable>

        <Pressable
          onPress={handleUploadImage}
          disabled={isLoading}
          className="bg-green-600 p-4 rounded-lg"
        >
          {isLoading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text className="text-white font-bold text-center">
              🖼 Upload Image
            </Text>
          )}
        </Pressable>

        {questions.length > 0 && (
          <View className="mt-4">
            <Text className="text-lg font-bold text-foreground mb-2">
              Extracted Questions: {questions.length}
            </Text>
            {questions.map((q, index) => (
              <View key={index} className="bg-surface p-3 rounded-lg mb-2">
                <Text className="font-bold text-foreground">
                  {q.question}
                </Text>
                <Text className="text-sm text-muted mt-1">
                  Subject: {q.subject} | Lesson: {q.lesson}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
}
```

## Deployment

### Local Network

For testing on local network:

```bash
# Get your machine IP
ipconfig getifaddr en0  # macOS
hostname -I  # Linux
ipconfig  # Windows

# Start server
python main.py server --host 0.0.0.0 --port 8000

# In React Native app, use:
const AI_ENGINE_API = "http://192.168.1.100:8000";
```

### Production Deployment

For production, deploy the Medical AI Engine to a server:

```bash
# Using Docker
docker build -t medical-ai-engine .
docker run -p 8000:8000 medical-ai-engine

# Using Heroku
heroku create medical-ai-engine
git push heroku main

# Using Railway, Render, or other services
# Follow their deployment guides
```

Update React Native app with production URL:

```typescript
const AI_ENGINE_API = process.env.NODE_ENV === 'production'
  ? "https://medical-ai-engine.example.com"
  : "http://localhost:8000";
```

## Error Handling

Implement proper error handling in your app:

```typescript
async function extractWithErrorHandling(file) {
  try {
    setIsLoading(true);
    
    const response = await fetch(`${AI_ENGINE_API}/extract/pdf`, {
      method: "POST",
      body: formData,
      timeout: 60000, // 60 second timeout
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.questions || data.questions.length === 0) {
      Alert.alert("No Questions", "Could not extract any questions from the file");
      return;
    }

    // Process questions
    for (const question of data.questions) {
      await addQuestion(question);
    }

    Alert.alert("Success", `Extracted ${data.total_extracted} questions`);
  } catch (error) {
    if (error.message.includes("timeout")) {
      Alert.alert("Timeout", "Request took too long. Try a smaller file.");
    } else if (error.message.includes("Network")) {
      Alert.alert("Network Error", "Check your internet connection");
    } else {
      Alert.alert("Error", error.message);
    }
  } finally {
    setIsLoading(false);
  }
}
```

## Performance Optimization

### 1. Caching

Cache extracted questions to avoid re-processing:

```typescript
const cache = new Map();

async function extractWithCache(fileHash) {
  if (cache.has(fileHash)) {
    return cache.get(fileHash);
  }

  const questions = await extract(file);
  cache.set(fileHash, questions);
  return questions;
}
```

### 2. Batch Processing

Process multiple files in parallel:

```typescript
async function processBatch(files) {
  const promises = files.map(file => extract(file));
  return Promise.all(promises);
}
```

### 3. Compression

Compress large files before upload:

```typescript
import { compress } from "react-native-image-compress";

const compressedImage = await compress(imagePath);
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
curl http://your-server:8000/health

# Check firewall
sudo ufw allow 8000
```

### Slow Extraction

- Use smaller files
- Enable GPU in Medical AI Engine
- Increase timeout in React Native app

### Database Issues

```bash
# Reset database
rm medical_questions.db

# Check database
sqlite3 medical_questions.db ".tables"
```

## Support

For issues or questions, refer to:
- Medical AI Engine README: `/home/ubuntu/medical-ai-engine/README.md`
- FastAPI Docs: `http://your-server:8000/docs`
- OKSmed Documentation: `/home/ubuntu/medical-quiz-app/README_OKSMED.md`
