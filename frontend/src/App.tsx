import React, { useState, useCallback } from 'react';
import { HomeScreen } from './screens/HomeScreen';
import { AskScreen } from './screens/AskScreen';
import { PrepScreen } from './screens/PrepScreen';
import { LookupScreen } from './screens/LookupScreen';
import { IndustryDetailScreen } from './screens/IndustryDetailScreen';
import { BriefScreen } from './screens/BriefScreen';
import { LossRunScreen } from './screens/LossRunScreen';
import { ExperienceModScreen } from './screens/ExperienceModScreen';
import { AccountReviewScreen } from './screens/AccountReviewScreen';

interface NavState {
  screen: string;
  params?: any;
}

export default function App() {
  const [navStack, setNavStack] = useState<NavState[]>([{ screen: 'home' }]);

  const current = navStack[navStack.length - 1];

  const navigate = useCallback(
    (screen: string, params?: any) => {
      setNavStack((prev) => [...prev, { screen, params }]);
    },
    []
  );

  const goBack = useCallback(() => {
    setNavStack((prev) => (prev.length > 1 ? prev.slice(0, -1) : prev));
  }, []);

  const goHome = useCallback(() => {
    setNavStack([{ screen: 'home' }]);
  }, []);

  switch (current.screen) {
    case 'home':
      return <HomeScreen onNavigate={navigate} />;
    case 'ask':
      return (
        <AskScreen
          onNavigate={navigate}
          onBack={goBack}
          prefill={current.params?.prefill}
        />
      );
    case 'prep':
      return <PrepScreen onNavigate={navigate} onBack={goBack} />;
    case 'lookup':
      return <LookupScreen onNavigate={navigate} onBack={goBack} />;
    case 'industryDetail':
      return (
        <IndustryDetailScreen
          industryId={current.params?.industryId}
          onNavigate={navigate}
          onBack={goBack}
        />
      );
    case 'brief':
      return (
        <BriefScreen
          briefId={current.params?.briefId}
          onBack={goHome}
          onNavigate={navigate}
        />
      );
    case 'lossRuns':
      return <LossRunScreen onNavigate={navigate} onBack={goBack} />;
    case 'experienceMod':
      return <ExperienceModScreen onNavigate={navigate} onBack={goBack} />;
    case 'accountReview':
      return <AccountReviewScreen onNavigate={navigate} onBack={goBack} />;
    default:
      return <HomeScreen onNavigate={navigate} />;
  }
}
