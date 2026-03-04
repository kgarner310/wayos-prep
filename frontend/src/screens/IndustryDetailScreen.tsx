import React, { useState, useEffect } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Section } from '../components/Section';
import { colors } from '../services/theme';
import { api, IndustryDetail } from '../services/api';

interface IndustryDetailScreenProps {
  industryId: number;
  onNavigate: (screen: string, params?: any) => void;
  onBack: () => void;
}

export function IndustryDetailScreen({
  industryId,
  onNavigate,
  onBack,
}: IndustryDetailScreenProps) {
  const [industry, setIndustry] = useState<IndustryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .getIndustry(industryId)
      .then(setIndustry)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [industryId]);

  const handleGenerate = async () => {
    if (!industry) return;
    setGenerating(true);
    try {
      const brief = await api.prepBrief({
        industry: industry.industry_name,
        location: 'Not specified',
      });
      onNavigate('brief', { briefId: brief.id });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 16, textAlign: 'center', color: colors.textLight }}>
        Loading...
      </div>
    );
  }

  if (error || !industry) {
    return (
      <div style={{ padding: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: colors.primary, fontSize: 13, fontWeight: 600, marginBottom: 12, padding: 0 }}>
          ← Back
        </button>
        <div style={{ color: colors.error, textAlign: 'center' }}>
          {error || 'Industry not found.'}
        </div>
      </div>
    );
  }

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

      <Card accentBorder>
        <div style={{ fontSize: 20, fontWeight: 800, color: colors.primary }}>
          {industry.industry_name}
        </div>
        {industry.synonyms.length > 0 && (
          <div
            style={{
              fontSize: 12,
              color: colors.textSecondary,
              fontStyle: 'italic',
              marginTop: 4,
            }}
          >
            Also: {industry.synonyms.join(', ')}
          </div>
        )}
      </Card>

      <Card>
        <Section title="Workers' Comp Claims" items={industry.top_workers_comp_claims} />
        <Section title="Commercial Auto Claims" items={industry.commercial_auto_claims} />
        <Section title="General Liability Exposures" items={industry.general_liability_exposures} />
        <Section title="Conversation Prompts" items={industry.conversation_prompts} />
        {industry.regional_risk_notes && (
          <Section title="Regional Risk Notes" text={industry.regional_risk_notes} />
        )}
      </Card>

      <Button
        title="Generate Brief"
        onClick={handleGenerate}
        loading={generating}
      />
    </div>
  );
}
