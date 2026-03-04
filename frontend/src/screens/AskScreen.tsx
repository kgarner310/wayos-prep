import React, { useState, useEffect } from 'react';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { colors } from '../services/theme';
import { api } from '../services/api';

interface AskScreenProps {
  onNavigate: (screen: string, params?: any) => void;
  onBack: () => void;
  prefill?: string;
}

export function AskScreen({ onNavigate, onBack, prefill }: AskScreenProps) {
  const [question, setQuestion] = useState(prefill || '');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (prefill) setQuestion(prefill);
  }, [prefill]);

  const handleGenerate = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError('');
    try {
      const brief = await api.askBrief(question, location || undefined);
      onNavigate('brief', { briefId: brief.id });
    } catch (err: any) {
      setError(err.message || 'Failed to generate brief');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 16 }}>
      <button
        onClick={onBack}
        style={{
          background: 'none',
          border: 'none',
          color: colors.primary,
          fontSize: 13,
          fontWeight: 600,
          marginBottom: 12,
          padding: 0,
        }}
      >
        ← Back
      </button>

      <div
        style={{
          fontSize: 18,
          fontWeight: 700,
          color: colors.primary,
          marginBottom: 16,
        }}
      >
        Ask Risk Question
      </div>

      <Input
        label="Your question"
        value={question}
        onChange={setQuestion}
        placeholder='e.g., "What risks should I discuss with a roofing contractor?"'
        multiline
      />

      <Input
        label="Location (optional)"
        value={location}
        onChange={setLocation}
        placeholder="e.g., North Carolina"
      />

      {error && (
        <div
          style={{
            color: colors.error,
            fontSize: 13,
            marginBottom: 12,
            padding: '8px 12px',
            background: '#FEF2F2',
            borderRadius: 8,
          }}
        >
          {error}
        </div>
      )}

      <Button
        title="Generate Brief"
        onClick={handleGenerate}
        loading={loading}
        disabled={!question.trim()}
      />
    </div>
  );
}
