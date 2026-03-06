import React, { useState } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Input } from '../components/Input';
import { Section } from '../components/Section';
import { colors } from '../services/theme';
import { api, LossRunAnalysisResponse } from '../services/api';

const LINES_OF_BUSINESS = [
  'Workers Comp',
  'General Liability',
  'Commercial Auto',
  'Property',
  'Umbrella',
  'Professional Liability',
  'Cyber',
  'BOP',
  'Inland Marine',
];

interface LineEntry {
  line_of_business: string;
  policy_year: string;
  premium: string;
  num_claims: string;
  total_incurred: string;
  total_paid: string;
  open_reserves: string;
  large_claims: string;
}

const emptyEntry = (): LineEntry => ({
  line_of_business: '',
  policy_year: '',
  premium: '',
  num_claims: '',
  total_incurred: '',
  total_paid: '',
  open_reserves: '',
  large_claims: '',
});

interface LossRunScreenProps {
  onNavigate: (screen: string, params?: any) => void;
  onBack: () => void;
}

export function LossRunScreen({ onNavigate, onBack }: LossRunScreenProps) {
  const [accountName, setAccountName] = useState('');
  const [entries, setEntries] = useState<LineEntry[]>([emptyEntry()]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<LossRunAnalysisResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const updateEntry = (index: number, field: keyof LineEntry, value: string) => {
    setEntries((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addEntry = () => setEntries((prev) => [...prev, emptyEntry()]);

  const removeEntry = (index: number) => {
    if (entries.length <= 1) return;
    setEntries((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAnalyze = async () => {
    if (!accountName) return;
    const validEntries = entries.filter((e) => e.line_of_business);
    if (validEntries.length === 0) return;

    setLoading(true);
    setError('');
    try {
      const data = await api.analyzeLossRuns({
        account_name: accountName,
        line_entries: validEntries.map((e) => ({
          line_of_business: e.line_of_business,
          policy_year: e.policy_year || undefined,
          premium: e.premium ? parseFloat(e.premium) : undefined,
          num_claims: e.num_claims ? parseInt(e.num_claims, 10) : undefined,
          total_incurred: e.total_incurred ? parseFloat(e.total_incurred) : undefined,
          total_paid: e.total_paid ? parseFloat(e.total_paid) : undefined,
          open_reserves: e.open_reserves ? parseFloat(e.open_reserves) : undefined,
          large_claims: e.large_claims
            ? e.large_claims.split('\n').filter((l) => l.trim())
            : undefined,
        })),
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze loss runs');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!result?.analysis_text) return;
    try {
      await navigator.clipboard.writeText(result.analysis_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = result.analysis_text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (result) {
    const analysis = result.analysis_json;
    const totals = analysis?.totals;
    const ratio = totals?.loss_ratio;

    return (
      <div style={{ padding: 16 }}>
        <button
          onClick={() => setResult(null)}
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
          ← Edit Data
        </button>

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
            WAYOS PREP — LOSS RUN REVIEW
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: colors.primary }}>
            {result.account_name}
          </div>
          {totals && (
            <div style={{ fontSize: 13, color: colors.textSecondary, marginTop: 4 }}>
              Premium: ${totals.premium?.toLocaleString()}
              {' • '}Incurred: ${totals.incurred?.toLocaleString()}
              {' • '}Claims: {totals.claims}
            </div>
          )}
          {ratio != null && (
            <div
              style={{
                fontSize: 14,
                fontWeight: 700,
                color: ratio > 0.6 ? colors.error : ratio < 0.4 ? colors.success : colors.text,
                marginTop: 4,
              }}
            >
              Overall Loss Ratio: {(ratio * 100).toFixed(0)}%
            </div>
          )}
        </Card>

        {/* Per-line summaries */}
        {analysis?.line_summaries?.length > 0 && (
          <Card>
            <Section title="By Line of Business" />
            {analysis.line_summaries.map((s: any, i: number) => {
              const lr = s.loss_ratio != null ? `${(s.loss_ratio * 100).toFixed(0)}%` : 'N/A';
              return (
                <div
                  key={i}
                  style={{
                    marginBottom: 10,
                    padding: '8px 0',
                    borderBottom: i < analysis.line_summaries.length - 1 ? `1px solid ${colors.border}` : 'none',
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600, color: colors.primary }}>
                    {s.line}
                  </div>
                  <div style={{ fontSize: 12, color: colors.textSecondary }}>
                    Premium: ${s.premium?.toLocaleString()} | Incurred: ${s.total_incurred?.toLocaleString()} | Claims: {s.num_claims} | LR: {lr}
                  </div>
                  {s.open_reserves > 0 && (
                    <div style={{ fontSize: 12, color: colors.accent }}>
                      Open Reserves: ${s.open_reserves?.toLocaleString()}
                    </div>
                  )}
                </div>
              );
            })}
          </Card>
        )}

        {/* Flags */}
        {analysis?.flags?.length > 0 && (
          <Card>
            <Section title="Flags & Concerns" items={analysis.flags} />
          </Card>
        )}

        {/* Talking Points */}
        {analysis?.talking_points?.length > 0 && (
          <Card>
            <Section title="Producer Talking Points" items={analysis.talking_points} />
          </Card>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
          <Button
            title={copied ? 'Copied!' : 'Copy Analysis'}
            onClick={handleCopy}
            variant={copied ? 'accent' : 'secondary'}
          />
          <Button title="New Analysis" onClick={onBack} variant="outline" />
        </div>

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
          marginBottom: 4,
        }}
      >
        Loss Run Review
      </div>
      <div
        style={{
          fontSize: 12,
          color: colors.textSecondary,
          marginBottom: 16,
        }}
      >
        Enter loss run data across all lines for analysis and talking points.
      </div>

      <Input
        label="Account Name *"
        value={accountName}
        onChange={setAccountName}
        placeholder="e.g., ABC Manufacturing"
      />

      {entries.map((entry, index) => (
        <Card key={index} style={{ marginBottom: 12 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 8,
            }}
          >
            <div
              style={{
                fontSize: 12,
                fontWeight: 700,
                color: colors.primary,
                textTransform: 'uppercase',
              }}
            >
              Line {index + 1}
            </div>
            {entries.length > 1 && (
              <button
                onClick={() => removeEntry(index)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: colors.error,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                Remove
              </button>
            )}
          </div>

          {/* Line of business picker */}
          <div style={{ marginBottom: 8 }}>
            <label
              style={{
                display: 'block',
                fontSize: 11,
                fontWeight: 600,
                color: colors.textSecondary,
                marginBottom: 3,
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Line of Business *
            </label>
            <select
              value={entry.line_of_business}
              onChange={(e) => updateEntry(index, 'line_of_business', e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                borderRadius: 8,
                border: `1.5px solid ${colors.border}`,
                background: colors.surface,
                color: colors.text,
                fontSize: 13,
              }}
            >
              <option value="">Select...</option>
              {LINES_OF_BUSINESS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <Input
                label="Policy Year"
                value={entry.policy_year}
                onChange={(v) => updateEntry(index, 'policy_year', v)}
                placeholder="e.g., 2023"
              />
            </div>
            <div style={{ flex: 1 }}>
              <Input
                label="Premium"
                value={entry.premium}
                onChange={(v) => updateEntry(index, 'premium', v)}
                placeholder="$"
                type="number"
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <Input
                label="# Claims"
                value={entry.num_claims}
                onChange={(v) => updateEntry(index, 'num_claims', v)}
                placeholder="0"
                type="number"
              />
            </div>
            <div style={{ flex: 1 }}>
              <Input
                label="Total Incurred"
                value={entry.total_incurred}
                onChange={(v) => updateEntry(index, 'total_incurred', v)}
                placeholder="$"
                type="number"
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <Input
                label="Total Paid"
                value={entry.total_paid}
                onChange={(v) => updateEntry(index, 'total_paid', v)}
                placeholder="$"
                type="number"
              />
            </div>
            <div style={{ flex: 1 }}>
              <Input
                label="Open Reserves"
                value={entry.open_reserves}
                onChange={(v) => updateEntry(index, 'open_reserves', v)}
                placeholder="$"
                type="number"
              />
            </div>
          </div>

          <Input
            label="Large/Notable Claims"
            value={entry.large_claims}
            onChange={(v) => updateEntry(index, 'large_claims', v)}
            placeholder="One per line..."
            multiline
          />
        </Card>
      ))}

      <Button title="+ Add Line" onClick={addEntry} variant="outline" small />

      {error && (
        <div
          style={{
            color: colors.error,
            fontSize: 13,
            marginTop: 12,
            padding: '8px 12px',
            background: '#FEF2F2',
            borderRadius: 8,
          }}
        >
          {error}
        </div>
      )}

      <div style={{ marginTop: 12 }}>
        <Button
          title="Analyze Loss Runs"
          onClick={handleAnalyze}
          loading={loading}
          disabled={!accountName || entries.every((e) => !e.line_of_business)}
        />
      </div>
    </div>
  );
}
