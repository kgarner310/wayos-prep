import React, { useState, useEffect } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Section } from '../components/Section';
import { colors } from '../services/theme';
import { api, BriefResponse } from '../services/api';
import { composeEmailWithBody, isOutlookContext } from '../services/office';

interface BriefScreenProps {
  briefId: number;
  onBack: () => void;
  onNavigate: (screen: string, params?: any) => void;
}

export function BriefScreen({ briefId, onBack, onNavigate }: BriefScreenProps) {
  const [brief, setBrief] = useState<BriefResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showSendPack, setShowSendPack] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api
      .getBrief(briefId)
      .then(setBrief)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [briefId]);

  const handleCopy = async () => {
    if (!brief) return;
    try {
      await navigator.clipboard.writeText(brief.brief_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: select-all in a textarea
      const ta = document.createElement('textarea');
      ta.value = brief.brief_text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSendUnderwriterEmail = async () => {
    if (!brief) return;
    const bj = brief.brief_json;
    const subject = `${bj.industry} Risk Notes and Questions`;

    if (isOutlookContext()) {
      await composeEmailWithBody(subject, brief.underwriter_email_text);
    } else {
      await navigator.clipboard.writeText(brief.underwriter_email_text);
      alert('Underwriter email copied to clipboard.');
    }
    setShowSendPack(false);
  };

  const handleSendInternalNote = async () => {
    if (!brief) return;

    if (isOutlookContext()) {
      await composeEmailWithBody('WAYOS PREP — Account Prep', brief.internal_note_text);
    } else {
      await navigator.clipboard.writeText(brief.internal_note_text);
      alert('Internal note copied to clipboard.');
    }
    setShowSendPack(false);
  };

  const handleFeedback = async (helpful: boolean) => {
    if (!brief || feedbackGiven) return;
    try {
      await api.submitFeedback({
        query_log_id: brief.id,
        helpful_bool: helpful,
      });
      setFeedbackGiven(true);
    } catch {}
  };

  if (loading) {
    return (
      <div style={{ padding: 16, textAlign: 'center', color: colors.textLight }}>
        Generating brief...
      </div>
    );
  }

  if (error || !brief) {
    return (
      <div style={{ padding: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: colors.primary, fontSize: 13, fontWeight: 600, marginBottom: 12, padding: 0 }}>
          ← Back
        </button>
        <div style={{ color: colors.error, textAlign: 'center' }}>
          {error || 'Brief not found.'}
        </div>
      </div>
    );
  }

  const bj = brief.brief_json;

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

      {/* Header */}
      <Card accentBorder>
        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            color: colors.accent,
            textTransform: 'uppercase',
            letterSpacing: 1.5,
            marginBottom: 4,
          }}
        >
          WAYOS PREP — CLIENT BRIEF
        </div>
        <div style={{ fontSize: 20, fontWeight: 800, color: colors.primary }}>
          {bj.industry}
        </div>
        <div style={{ fontSize: 13, color: colors.textSecondary, marginTop: 2 }}>
          {bj.location}
          {bj.employee_count && ` • ${bj.employee_count} employees`}
        </div>
        {(bj.mod || bj.vehicle_exposure) && (
          <div style={{ fontSize: 12, color: colors.textSecondary }}>
            {bj.mod && `MOD: ${bj.mod}`}
            {bj.mod && bj.vehicle_exposure && ' • '}
            {bj.vehicle_exposure && `Vehicles: ${bj.vehicle_exposure}`}
          </div>
        )}
        <div style={{ fontSize: 11, color: colors.textLight, marginTop: 4 }}>
          {bj.generated_at}
        </div>
      </Card>

      {/* Brief sections */}
      <Card>
        <Section title="Top Claim Drivers (what actually hurts)" items={bj.top_claim_drivers} />
        <Section title="Regional / Local Risk Notes" text={bj.regional_risk_notes} />
        <Section title="Coverage Exposures (what to stress-test)" items={bj.coverage_exposures} />
        <Section title="Conversation Starters (producer ammo)" items={bj.conversation_starters} />
        <Section title="Quick Docs to Request" items={bj.docs_to_request} />
      </Card>

      {/* Actions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
        <Button
          title={copied ? 'Copied!' : 'Copy Brief'}
          onClick={handleCopy}
          variant={copied ? 'accent' : 'secondary'}
        />
        <Button
          title={isOutlookContext() ? 'Send Pack (Email)' : 'Send Pack'}
          onClick={() => setShowSendPack(!showSendPack)}
          variant="primary"
        />
      </div>

      {/* Send Pack panel */}
      {showSendPack && (
        <Card style={{ border: `1.5px solid ${colors.accent}` }}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: colors.primary,
              marginBottom: 4,
            }}
          >
            Send Pack
          </div>
          <div
            style={{
              fontSize: 12,
              color: colors.textSecondary,
              marginBottom: 12,
            }}
          >
            {isOutlookContext()
              ? 'Opens a new email with the formatted message.'
              : 'Copies the formatted message to your clipboard.'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <Button
              title="Underwriter Email"
              onClick={handleSendUnderwriterEmail}
              variant="primary"
              small
            />
            <Button
              title="Internal Note (CSR)"
              onClick={handleSendInternalNote}
              variant="secondary"
              small
            />
          </div>
        </Card>
      )}

      {/* Feedback */}
      {!feedbackGiven ? (
        <Card style={{ textAlign: 'center' }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: colors.text,
              marginBottom: 10,
            }}
          >
            Was this brief helpful?
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 24 }}>
            <button
              onClick={() => handleFeedback(true)}
              style={{
                background: 'none',
                border: 'none',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2,
                cursor: 'pointer',
              }}
            >
              <span style={{ fontSize: 24 }}>👍</span>
              <span style={{ fontSize: 11, color: colors.textSecondary }}>Helpful</span>
            </button>
            <button
              onClick={() => handleFeedback(false)}
              style={{
                background: 'none',
                border: 'none',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2,
                cursor: 'pointer',
              }}
            >
              <span style={{ fontSize: 24 }}>👎</span>
              <span style={{ fontSize: 11, color: colors.textSecondary }}>Not Helpful</span>
            </button>
          </div>
        </Card>
      ) : (
        <Card style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: colors.success }}>
            Thanks for your feedback!
          </div>
        </Card>
      )}

      <div
        style={{
          textAlign: 'center',
          fontSize: 11,
          color: colors.textLight,
          marginTop: 12,
          marginBottom: 24,
        }}
      >
        Prepared with WAYOS PREP • wayosprep.app
      </div>
    </div>
  );
}
