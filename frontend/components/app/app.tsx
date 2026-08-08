'use client';

import { useMemo } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { useMicrophonePermission } from '@/hooks/useMicrophonePermission';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

/**
 * Mic error banner — displayed when microphone permission is denied or unavailable
 */
function MicErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div className="fixed top-0 left-0 z-[100] w-full px-4 pt-3 md:px-6 md:pt-4">
      <div className="agri-mic-error-banner mx-auto flex max-w-2xl items-start gap-3">
        <span className="mt-0.5 text-lg" role="img" aria-label="Warning">
          ⚠️
        </span>
        <div className="flex-1">
          <p className="text-sm font-semibold leading-relaxed">
            मायक्रोफोन परवानगी नाकारली
          </p>
          <p className="mt-1 text-xs leading-relaxed opacity-90">
            Microphone access blocked. Please allow mic access in your browser settings to talk to AgriAlert.
          </p>
          <p className="mt-2 text-xs opacity-70">
            ब्राउझर सेटिंग्जमध्ये मायक्रोफोन परवानगी द्या
          </p>
        </div>
        <button
          onClick={onDismiss}
          className="hover:bg-foreground/10 mt-0.5 rounded-full p-1 text-sm transition-colors"
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const { errorMessage, dismissError } = useMicrophonePermission();

  const tokenSource = useMemo(() => {
    return typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string'
      ? getSandboxTokenSource(appConfig)
      : TokenSource.endpoint('/api/token');
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />

      {/* Microphone Error Banner */}
      {errorMessage && (
        <MicErrorBanner message={errorMessage} onDismiss={dismissError} />
      )}

      <main className="grid h-svh grid-cols-1 place-content-center">
        <ViewController appConfig={appConfig} />
      </main>
      <StartAudioButton label="ऑडिओ सुरू करा / Start Audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
