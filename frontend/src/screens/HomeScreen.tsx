import React, { useEffect, useState } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { colors } from '../services/theme';
import { getAppointmentSubject, isOutlookContext } from '../services/office';

interface HomeScreenProps {
  onNavigate: (screen: string, params?: any) => void;
}

export function HomeScreen({ onNavigate }: HomeScreenProps) {
  const [calendarHint, setCalendarHint] = useState<string | null>(null);

  useEffect(() => {
    getAppointmentSubject().then((subject) => {
      if (subject) setCalendarHint(subject);
    });
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ textAlign: 'center', marginBottom: 20, marginTop: 8 }}>
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: colors.accent,
            textTransform: 'uppercase',
            letterSpacing: 2,
            marginBottom: 4,
          }}
        >
          WAYOS PREP
        </div>
        <div
          style={{
            fontSize: 20,
            fontWeight: 800,
            color: colors.primary,
            lineHeight: 1.3,
          }}
        >
          Meeting Prep Engine
        </div>
        <div
          style={{ fontSize: 12, color: colors.textSecondary, marginTop: 4 }}
        >
          Better meetings. Better coverage.
        </div>
      </div>

      {calendarHint && (
        <Card accentBorder>
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: colors.accent,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              marginBottom: 4,
            }}
          >
            From your calendar
          </div>
          <div
            style={{
              fontSize: 13,
              color: colors.text,
              fontWeight: 500,
              marginBottom: 10,
            }}
          >
            {calendarHint}
          </div>
          <Button
            title="Prep This Meeting"
            onClick={() => onNavigate('ask', { prefill: calendarHint })}
            variant="accent"
            small
          />
        </Card>
      )}

      {isOutlookContext() && !calendarHint && (
        <Card>
          <div style={{ fontSize: 12, color: colors.textLight, textAlign: 'center' }}>
            Open from a calendar invite to auto-detect the account.
          </div>
        </Card>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <Button
          title="Ask Risk Question"
          onClick={() => onNavigate('ask')}
          variant="primary"
        />
        <Button
          title="Prep This Account"
          onClick={() => onNavigate('prep')}
          variant="primary"
        />
        <Button
          title="Industry Lookup"
          onClick={() => onNavigate('lookup')}
          variant="secondary"
        />
      </div>
    </div>
  );
}
