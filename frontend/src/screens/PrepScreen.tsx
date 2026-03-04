import React, { useState, useEffect } from 'react';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { colors } from '../services/theme';
import { api, IndustryListItem } from '../services/api';

interface PrepScreenProps {
  onNavigate: (screen: string, params?: any) => void;
  onBack: () => void;
}

export function PrepScreen({ onNavigate, onBack }: PrepScreenProps) {
  const [industries, setIndustries] = useState<IndustryListItem[]>([]);
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [employees, setEmployees] = useState('');
  const [mod, setMod] = useState('');
  const [vehicleExposure, setVehicleExposure] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPicker, setShowPicker] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.listIndustries().then(setIndustries).catch(() => {});
  }, []);

  const filtered = industries.filter((i) =>
    i.industry_name.toLowerCase().includes(search.toLowerCase())
  );

  const handleGenerate = async () => {
    if (!industry || !location) return;
    setLoading(true);
    setError('');
    try {
      const brief = await api.prepBrief({
        industry,
        location,
        employee_count: employees ? parseInt(employees, 10) : undefined,
        mod: mod ? parseFloat(mod) : undefined,
        vehicle_exposure: vehicleExposure || undefined,
      });
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
        Prep This Account
      </div>

      {/* Industry picker */}
      <div style={{ marginBottom: 12 }}>
        <label
          style={{
            display: 'block',
            fontSize: 12,
            fontWeight: 600,
            color: colors.textSecondary,
            marginBottom: 4,
            textTransform: 'uppercase',
            letterSpacing: 0.5,
          }}
        >
          Industry *
        </label>
        <button
          onClick={() => setShowPicker(!showPicker)}
          style={{
            width: '100%',
            padding: '10px 12px',
            borderRadius: 8,
            border: `1.5px solid ${colors.border}`,
            background: colors.surface,
            color: industry ? colors.text : colors.textLight,
            fontSize: 14,
            textAlign: 'left',
          }}
        >
          {industry || 'Select an industry...'}
        </button>

        {showPicker && (
          <div
            style={{
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              marginTop: 4,
              maxHeight: 200,
              overflow: 'auto',
              background: colors.surface,
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ padding: '8px 8px 4px', position: 'sticky', top: 0, background: colors.surface }}>
              <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{
                  width: '100%',
                  padding: '6px 10px',
                  borderRadius: 6,
                  border: `1px solid ${colors.border}`,
                  fontSize: 13,
                  outline: 'none',
                }}
                autoFocus
              />
            </div>
            {filtered.map((ind) => (
              <button
                key={ind.id}
                onClick={() => {
                  setIndustry(ind.industry_name);
                  setShowPicker(false);
                  setSearch('');
                }}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '8px 12px',
                  border: 'none',
                  background:
                    ind.industry_name === industry
                      ? colors.background
                      : 'transparent',
                  color: colors.text,
                  fontSize: 13,
                  textAlign: 'left',
                  cursor: 'pointer',
                }}
              >
                {ind.industry_name}
              </button>
            ))}
          </div>
        )}
      </div>

      <Input
        label="Location *"
        value={location}
        onChange={setLocation}
        placeholder="e.g., North Carolina"
      />

      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <Input
            label="Employees"
            value={employees}
            onChange={setEmployees}
            placeholder="e.g., 12"
            type="number"
          />
        </div>
        <div style={{ flex: 1 }}>
          <Input
            label="MOD"
            value={mod}
            onChange={setMod}
            placeholder="e.g., 1.15"
            type="number"
          />
        </div>
      </div>

      <Input
        label="Vehicle Exposure"
        value={vehicleExposure}
        onChange={setVehicleExposure}
        placeholder="e.g., 3 trucks"
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
        disabled={!industry || !location}
      />
    </div>
  );
}
