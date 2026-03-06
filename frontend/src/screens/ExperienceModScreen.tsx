import React, { useState } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Input } from '../components/Input';
import { Section } from '../components/Section';
import { colors } from '../services/theme';
import { api, ExperienceModAnalysisResponse } from '../services/api';

interface ModClaim {
  claim_number: string;
  year: string;
  description: string;
  incurred: string;
  medical_only: boolean;
}

const emptyClaim = (): ModClaim => ({
  claim_number: '',
  year: '',
  description: '',
  incurred: '',
  medical_only: false,
});

interface ExperienceModScreenProps {
  onNavigate: (screen: string, params?: any) => void;
  onBack: () => void;
}

export function ExperienceModScreen({ onNavigate, onBack }: ExperienceModScreenProps) {
  const [accountName, setAccountName] = useState('');
  const [currentMod, setCurrentMod] = useState('');
  const [priorMod, setPriorMod] = useState('');
  const [expectedLosses, setExpectedLosses] = useState('');
  const [actualPrimary, setActualPrimary] = useState('');
  const [actualExcess, setActualExcess] = useState('');
  const [totalPayroll, setTotalPayroll] = useState('');
  const [claims, setClaims] = useState<ModClaim[]>([emptyClaim()]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ExperienceModAnalysisResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const updateClaim = (index: number, field: keyof ModClaim, value: any) => {
    setClaims((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addClaim = () => setClaims((prev) => [...prev, emptyClaim()]);

  const removeClaim = (index: number) => {
    if (claims.length <= 1) return;
    setClaims((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAnalyze = async () => {
    if (!accountName || !currentMod) return;
    setLoading(true);
    setError('');
    try {
      const validClaims = claims.filter((c) => c.description || c.incurred);
      const data = await api.analyzeExperienceMod({
        account_name: accountName,
        current_mod: parseFloat(currentMod),
        prior_mod: priorMod ? parseFloat(priorMod) : undefined,
        expected_losses: expectedLosses ? parseFloat(expectedLosses) : undefined,
        actual_primary_losses: actualPrimary ? parseFloat(actualPrimary) : undefined,
        actual_excess_losses: actualExcess ? parseFloat(actualExcess) : undefined,
        total_payroll: totalPayroll ? parseFloat(totalPayroll) : undefined,
        mod_claims: validClaims.length > 0
          ? validClaims.map((c) => ({
              claim_number: c.claim_number || undefined,
              year: c.year || undefined,
              description: c.description || undefined,
              incurred: c.incurred ? parseFloat(c.incurred) : undefined,
              medical_only: c.medical_only,
            }))
          : undefined,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze experience mod');
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
    const trend = analysis?.mod_trend;

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
            WAYOS PREP — EXPERIENCE MOD REVIEW
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: colors.primary }}>
            {result.account_name}
          </div>
          <div
            style={{
              fontSize: 24,
              fontWeight: 800,
              color:
                result.current_mod != null && result.current_mod > 1.0
                  ? colors.error
                  : colors.success,
              marginTop: 4,
            }}
          >
            MOD: {result.current_mod?.toFixed(2)}
          </div>
          {trend && (
            <div
              style={{
                fontSize: 13,
                color:
                  trend.direction === 'improving'
                    ? colors.success
                    : trend.direction === 'worsening'
                    ? colors.error
                    : colors.textSecondary,
                fontWeight: 600,
                marginTop: 2,
              }}
            >
              {trend.direction === 'improving' && '↓ '}
              {trend.direction === 'worsening' && '↑ '}
              {trend.direction.charAt(0).toUpperCase() + trend.direction.slice(1)} (
              {trend.change > 0 ? '+' : ''}
              {trend.change?.toFixed(2)} from {result.prior_mod?.toFixed(2)})
            </div>
          )}
        </Card>

        {/* Loss Analysis */}
        {analysis?.loss_analysis && (
          <Card>
            <Section title="Expected vs Actual Losses" />
            <div style={{ fontSize: 13, color: colors.text, lineHeight: 1.8 }}>
              <div>Expected: ${analysis.loss_analysis.expected_losses?.toLocaleString()}</div>
              <div>Actual Primary: ${analysis.loss_analysis.actual_primary?.toLocaleString()}</div>
              <div>Actual Excess: ${analysis.loss_analysis.actual_excess?.toLocaleString()}</div>
              <div style={{ fontWeight: 600 }}>
                Deviation: ${analysis.loss_analysis.deviation?.toLocaleString()} (
                {((analysis.loss_analysis.deviation_pct || 0) * 100).toFixed(0)}%)
              </div>
            </div>
          </Card>
        )}

        {/* Claims on worksheet */}
        {analysis?.claims_analysis?.length > 0 && (
          <Card>
            <Section title="Claims on Worksheet (by impact)" />
            {analysis.claims_analysis.map((c: any, i: number) => (
              <div
                key={i}
                style={{
                  padding: '6px 0',
                  borderBottom:
                    i < analysis.claims_analysis.length - 1
                      ? `1px solid ${colors.border}`
                      : 'none',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600, color: colors.text }}>
                    {c.description || 'No description'}
                    {c.medical_only && (
                      <span
                        style={{
                          fontSize: 10,
                          background: colors.success,
                          color: '#fff',
                          padding: '1px 5px',
                          borderRadius: 4,
                          marginLeft: 6,
                        }}
                      >
                        MED ONLY
                      </span>
                    )}
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color:
                        c.mod_impact === 'high'
                          ? colors.error
                          : c.mod_impact === 'medium'
                          ? colors.accent
                          : colors.success,
                    }}
                  >
                    {c.mod_impact?.toUpperCase()}
                  </div>
                </div>
                <div style={{ fontSize: 12, color: colors.textSecondary }}>
                  ${(c.incurred || 0).toLocaleString()}
                  {c.year && ` • ${c.year}`}
                </div>
              </div>
            ))}
          </Card>
        )}

        {/* Flags */}
        {analysis?.flags?.length > 0 && (
          <Card>
            <Section title="Flags & Concerns" items={analysis.flags} />
          </Card>
        )}

        {/* Positive indicators */}
        {analysis?.insights?.length > 0 && (
          <Card>
            <Section title="Positive Indicators" items={analysis.insights} />
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
        Experience Mod Review
      </div>
      <div
        style={{
          fontSize: 12,
          color: colors.textSecondary,
          marginBottom: 16,
        }}
      >
        Enter mod worksheet data to identify what's driving the mod and find opportunities.
      </div>

      <Input
        label="Account Name *"
        value={accountName}
        onChange={setAccountName}
        placeholder="e.g., ABC Manufacturing"
      />

      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <Input
            label="Current Mod *"
            value={currentMod}
            onChange={setCurrentMod}
            placeholder="e.g., 1.15"
            type="number"
          />
        </div>
        <div style={{ flex: 1 }}>
          <Input
            label="Prior Mod"
            value={priorMod}
            onChange={setPriorMod}
            placeholder="e.g., 1.05"
            type="number"
          />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <Input
            label="Expected Losses"
            value={expectedLosses}
            onChange={setExpectedLosses}
            placeholder="$"
            type="number"
          />
        </div>
        <div style={{ flex: 1 }}>
          <Input
            label="Total Payroll"
            value={totalPayroll}
            onChange={setTotalPayroll}
            placeholder="$"
            type="number"
          />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <Input
            label="Actual Primary Losses"
            value={actualPrimary}
            onChange={setActualPrimary}
            placeholder="$"
            type="number"
          />
        </div>
        <div style={{ flex: 1 }}>
          <Input
            label="Actual Excess Losses"
            value={actualExcess}
            onChange={setActualExcess}
            placeholder="$"
            type="number"
          />
        </div>
      </div>

      {/* Claims section */}
      <div
        style={{
          fontSize: 14,
          fontWeight: 700,
          color: colors.primary,
          marginTop: 16,
          marginBottom: 8,
        }}
      >
        Claims on Worksheet
      </div>

      {claims.map((claim, index) => (
        <Card key={index} style={{ marginBottom: 10 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 6,
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
              Claim {index + 1}
            </div>
            {claims.length > 1 && (
              <button
                onClick={() => removeClaim(index)}
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

          <Input
            label="Description"
            value={claim.description}
            onChange={(v) => updateClaim(index, 'description', v)}
            placeholder="e.g., Back injury — warehouse"
          />

          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <Input
                label="Incurred"
                value={claim.incurred}
                onChange={(v) => updateClaim(index, 'incurred', v)}
                placeholder="$"
                type="number"
              />
            </div>
            <div style={{ flex: 1 }}>
              <Input
                label="Year"
                value={claim.year}
                onChange={(v) => updateClaim(index, 'year', v)}
                placeholder="e.g., 2023"
              />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
            <input
              type="checkbox"
              checked={claim.medical_only}
              onChange={(e) => updateClaim(index, 'medical_only', e.target.checked)}
              style={{ width: 16, height: 16 }}
            />
            <label style={{ fontSize: 13, color: colors.text }}>Medical Only</label>
          </div>
        </Card>
      ))}

      <Button title="+ Add Claim" onClick={addClaim} variant="outline" small />

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
          title="Analyze Mod Worksheet"
          onClick={handleAnalyze}
          loading={loading}
          disabled={!accountName || !currentMod}
        />
      </div>
    </div>
  );
}
