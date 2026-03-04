import React, { useState, useEffect } from 'react';
import { colors } from '../services/theme';
import { api, IndustryListItem } from '../services/api';

interface LookupScreenProps {
  onNavigate: (screen: string, params?: any) => void;
  onBack: () => void;
}

export function LookupScreen({ onNavigate, onBack }: LookupScreenProps) {
  const [industries, setIndustries] = useState<IndustryListItem[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listIndustries()
      .then(setIndustries)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = industries.filter((i) =>
    i.industry_name.toLowerCase().includes(search.toLowerCase())
  );

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
          marginBottom: 12,
        }}
      >
        Industry Lookup
      </div>

      <input
        type="text"
        placeholder="Search industries..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{
          width: '100%',
          padding: '10px 12px',
          borderRadius: 8,
          border: `1.5px solid ${colors.border}`,
          background: colors.surface,
          fontSize: 14,
          marginBottom: 12,
          outline: 'none',
        }}
      />

      {loading && (
        <div style={{ textAlign: 'center', color: colors.textLight, padding: 20 }}>
          Loading...
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div style={{ textAlign: 'center', color: colors.textLight, padding: 20 }}>
          No industries found.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {filtered.map((ind) => (
          <button
            key={ind.id}
            onClick={() => onNavigate('industryDetail', { industryId: ind.id })}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 12px',
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              cursor: 'pointer',
              transition: 'background 0.1s',
            }}
          >
            <span style={{ fontSize: 14, fontWeight: 500, color: colors.text }}>
              {ind.industry_name}
            </span>
            <span style={{ fontSize: 12, color: colors.textLight }}>→</span>
          </button>
        ))}
      </div>
    </div>
  );
}
