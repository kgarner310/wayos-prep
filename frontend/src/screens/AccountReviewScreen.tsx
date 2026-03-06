import React, { useState, useEffect } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Input } from '../components/Input';
import { Section } from '../components/Section';
import { colors } from '../services/theme';
import { api, AccountListItem, AccountDetail } from '../services/api';

interface AccountReviewScreenProps {
  onNavigate: (screen: string, params?: any) => void;
  onBack: () => void;
}

type View = 'list' | 'create' | 'detail';

export function AccountReviewScreen({ onNavigate, onBack }: AccountReviewScreenProps) {
  const [view, setView] = useState<View>('list');
  const [accounts, setAccounts] = useState<AccountListItem[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<AccountDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Create form state
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [employees, setEmployees] = useState('');
  const [mod, setMod] = useState('');
  const [vehicleExposure, setVehicleExposure] = useState('');
  const [policyExpiration, setPolicyExpiration] = useState('');
  const [notes, setNotes] = useState('');
  const [generatingReview, setGeneratingReview] = useState(false);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const data = await api.listAccounts();
      setAccounts(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

  const handleCreate = async () => {
    if (!name) return;
    setLoading(true);
    setError('');
    try {
      const account = await api.createAccount({
        name,
        industry: industry || undefined,
        location: location || undefined,
        employee_count: employees ? parseInt(employees, 10) : undefined,
        current_mod: mod ? parseFloat(mod) : undefined,
        vehicle_exposure: vehicleExposure || undefined,
        policy_expiration: policyExpiration || undefined,
        notes: notes || undefined,
      });
      setSelectedAccount(account);
      setView('detail');
      // Reset form
      setName('');
      setIndustry('');
      setLocation('');
      setEmployees('');
      setMod('');
      setVehicleExposure('');
      setPolicyExpiration('');
      setNotes('');
    } catch (err: any) {
      setError(err.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAccount = async (accountId: number) => {
    setLoading(true);
    setError('');
    try {
      const account = await api.getAccount(accountId);
      setSelectedAccount(account);
      setView('detail');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReview = async () => {
    if (!selectedAccount) return;
    setGeneratingReview(true);
    setError('');
    try {
      const brief = await api.generateAccountReview(selectedAccount.id);
      onNavigate('brief', { briefId: brief.id });
    } catch (err: any) {
      setError(err.message || 'Failed to generate review');
    } finally {
      setGeneratingReview(false);
    }
  };

  // --- DETAIL VIEW ---
  if (view === 'detail' && selectedAccount) {
    const acct = selectedAccount;
    const hasLossRuns = acct.loss_run_reviews.length > 0;
    const hasMod = acct.experience_mod_reviews.length > 0;
    const hasBriefs = acct.briefs.length > 0;

    return (
      <div style={{ padding: 16 }}>
        <button
          onClick={() => { setView('list'); loadAccounts(); }}
          style={{
            background: 'none', border: 'none', color: colors.primary,
            fontSize: 13, fontWeight: 600, marginBottom: 12, padding: 0,
          }}
        >
          ← Accounts
        </button>

        <Card accentBorder>
          <div style={{
            fontSize: 10, fontWeight: 700, color: colors.accent,
            textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 4,
          }}>
            WAYOS PREP — ACCOUNT
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: colors.primary }}>
            {acct.name}
          </div>
          <div style={{ fontSize: 13, color: colors.textSecondary, marginTop: 2 }}>
            {acct.industry && acct.industry}
            {acct.industry && acct.location && ' • '}
            {acct.location && acct.location}
          </div>
          {acct.current_mod != null && (
            <div style={{
              fontSize: 14, fontWeight: 700, marginTop: 4,
              color: acct.current_mod > 1.0 ? colors.error : colors.success,
            }}>
              MOD: {acct.current_mod.toFixed(2)}
            </div>
          )}
          {acct.policy_expiration && (
            <div style={{ fontSize: 12, color: colors.accent, fontWeight: 600, marginTop: 4 }}>
              Policy Expiration: {acct.policy_expiration}
              {acct.renewal_status && ` (${acct.renewal_status})`}
            </div>
          )}
        </Card>

        {/* Quick actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
          <Button
            title={generatingReview ? 'Generating...' : 'Generate Full Account Review'}
            onClick={handleGenerateReview}
            loading={generatingReview}
            disabled={!acct.industry || !acct.location}
          />
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <Button
                title="Add Loss Runs"
                onClick={() => onNavigate('lossRuns')}
                variant="secondary"
                small
              />
            </div>
            <div style={{ flex: 1 }}>
              <Button
                title="Add Mod Review"
                onClick={() => onNavigate('experienceMod')}
                variant="secondary"
                small
              />
            </div>
          </div>
        </div>

        {(!acct.industry || !acct.location) && (
          <Card>
            <div style={{ fontSize: 12, color: colors.accent, textAlign: 'center' }}>
              Set industry and location to generate a full account review brief.
            </div>
          </Card>
        )}

        {/* Loss Run History */}
        <Card>
          <Section title={`Loss Run Reviews (${acct.loss_run_reviews.length})`} />
          {hasLossRuns ? (
            acct.loss_run_reviews.map((lr) => (
              <div
                key={lr.id}
                onClick={() => onNavigate('lossRunDetail', { reviewId: lr.id })}
                style={{
                  padding: '8px 0',
                  borderBottom: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: 13, color: colors.text }}>
                  {lr.total_claims != null ? `${lr.total_claims} claims` : 'Review'}
                  {lr.loss_ratio != null && ` • ${(lr.loss_ratio * 100).toFixed(0)}% LR`}
                  {lr.total_incurred != null && ` • $${lr.total_incurred.toLocaleString()} incurred`}
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: 12, color: colors.textLight }}>
              No loss run reviews yet.
            </div>
          )}
        </Card>

        {/* Mod History */}
        <Card>
          <Section title={`Experience Mod Reviews (${acct.experience_mod_reviews.length})`} />
          {hasMod ? (
            acct.experience_mod_reviews.map((mr) => (
              <div
                key={mr.id}
                style={{
                  padding: '8px 0',
                  borderBottom: `1px solid ${colors.border}`,
                }}
              >
                <div style={{ fontSize: 13, color: colors.text }}>
                  Mod: {mr.current_mod?.toFixed(2)}
                  {mr.prior_mod != null && ` (prior: ${mr.prior_mod.toFixed(2)})`}
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: 12, color: colors.textLight }}>
              No mod reviews yet.
            </div>
          )}
        </Card>

        {/* Prior Briefs */}
        {hasBriefs && (
          <Card>
            <Section title={`Prior Briefs (${acct.briefs.length})`} />
            {acct.briefs.map((b) => (
              <div
                key={b.id}
                onClick={() => onNavigate('brief', { briefId: b.id })}
                style={{
                  padding: '8px 0',
                  borderBottom: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: 12, color: colors.primary, fontWeight: 600 }}>
                  View Brief #{b.id} →
                </div>
              </div>
            ))}
          </Card>
        )}

        {acct.notes && (
          <Card>
            <Section title="Notes" text={acct.notes} />
          </Card>
        )}

        {error && (
          <div style={{
            color: colors.error, fontSize: 13, marginTop: 8,
            padding: '8px 12px', background: '#FEF2F2', borderRadius: 8,
          }}>
            {error}
          </div>
        )}

        <div style={{
          textAlign: 'center', fontSize: 11, color: colors.textLight,
          marginTop: 12, marginBottom: 24,
        }}>
          Prepared with WAYOS PREP • wayosprep.app
        </div>
      </div>
    );
  }

  // --- CREATE VIEW ---
  if (view === 'create') {
    return (
      <div style={{ padding: 16 }}>
        <button
          onClick={() => setView('list')}
          style={{
            background: 'none', border: 'none', color: colors.primary,
            fontSize: 13, fontWeight: 600, marginBottom: 12, padding: 0,
          }}
        >
          ← Back
        </button>

        <div style={{ fontSize: 18, fontWeight: 700, color: colors.primary, marginBottom: 4 }}>
          New Account
        </div>
        <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 16 }}>
          Create an account to track loss runs, mod reviews, and briefs in one place.
        </div>

        <Input label="Account Name *" value={name} onChange={setName} placeholder="e.g., ABC Manufacturing" />
        <Input label="Industry" value={industry} onChange={setIndustry} placeholder="e.g., Roofing" />
        <Input label="Location" value={location} onChange={setLocation} placeholder="e.g., Charlotte, NC" />

        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1 }}>
            <Input label="Employees" value={employees} onChange={setEmployees} placeholder="e.g., 25" type="number" />
          </div>
          <div style={{ flex: 1 }}>
            <Input label="Current Mod" value={mod} onChange={setMod} placeholder="e.g., 1.15" type="number" />
          </div>
        </div>

        <Input label="Vehicle Exposure" value={vehicleExposure} onChange={setVehicleExposure} placeholder="e.g., 5 trucks" />
        <Input label="Policy Expiration" value={policyExpiration} onChange={setPolicyExpiration} placeholder="e.g., 2026-06-15" />
        <Input label="Notes" value={notes} onChange={setNotes} placeholder="Account notes..." multiline />

        {error && (
          <div style={{
            color: colors.error, fontSize: 13, marginBottom: 12,
            padding: '8px 12px', background: '#FEF2F2', borderRadius: 8,
          }}>
            {error}
          </div>
        )}

        <Button title="Create Account" onClick={handleCreate} loading={loading} disabled={!name} />
      </div>
    );
  }

  // --- LIST VIEW ---
  return (
    <div style={{ padding: 16 }}>
      <button
        onClick={onBack}
        style={{
          background: 'none', border: 'none', color: colors.primary,
          fontSize: 13, fontWeight: 600, marginBottom: 12, padding: 0,
        }}
      >
        ← Back
      </button>

      <div style={{ fontSize: 18, fontWeight: 700, color: colors.primary, marginBottom: 4 }}>
        Accounts
      </div>
      <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 16 }}>
        Your saved accounts with loss runs, mod reviews, and briefs.
      </div>

      <Button title="+ New Account" onClick={() => setView('create')} variant="accent" small />

      {loading && (
        <div style={{ textAlign: 'center', color: colors.textLight, marginTop: 16, fontSize: 13 }}>
          Loading accounts...
        </div>
      )}

      {!loading && accounts.length === 0 && (
        <Card style={{ marginTop: 12 }}>
          <div style={{ fontSize: 13, color: colors.textLight, textAlign: 'center' }}>
            No accounts yet. Create one to start tracking.
          </div>
        </Card>
      )}

      {accounts.map((acct) => (
        <Card key={acct.id} style={{ cursor: 'pointer', marginTop: 8 }}>
          <div onClick={() => handleSelectAccount(acct.id)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: colors.primary }}>
                {acct.name}
              </div>
              {acct.current_mod != null && (
                <div style={{
                  fontSize: 12, fontWeight: 700,
                  color: acct.current_mod > 1.0 ? colors.error : colors.success,
                }}>
                  MOD {acct.current_mod.toFixed(2)}
                </div>
              )}
            </div>
            <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>
              {acct.industry || 'No industry'}
              {acct.location && ` • ${acct.location}`}
            </div>
            {acct.policy_expiration && (
              <div style={{ fontSize: 11, color: colors.accent, fontWeight: 600, marginTop: 4 }}>
                Expires: {acct.policy_expiration}
                {acct.renewal_status && ` • ${acct.renewal_status}`}
              </div>
            )}
          </div>
        </Card>
      ))}

      {error && (
        <div style={{
          color: colors.error, fontSize: 13, marginTop: 12,
          padding: '8px 12px', background: '#FEF2F2', borderRadius: 8,
        }}>
          {error}
        </div>
      )}
    </div>
  );
}
