'use client';

import { useCallback, useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { Button } from '@/components/ui/button';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

/**
 * Possible UI states for the AgriAlert voice agent
 */
type AgriViewState = 'ready' | 'connecting' | 'active' | 'ended';

interface ViewControllerProps {
  appConfig: AppConfig;
}

/**
 * Connecting state screen
 */
function ConnectingView() {
  return (
    <motion.div
      key="connecting"
      {...VIEW_MOTION_PROPS}
      className="bg-background flex flex-col items-center justify-center px-4 text-center"
    >
      <div className="agri-state-badge agri-state-badge--connecting mb-6">
        <div className="agri-spinner" />
        जोडत आहे... / Connecting...
      </div>

      <div className="mb-6">
        <div className="agri-spinner mx-auto" style={{ width: 48, height: 48, borderWidth: 4 }} />
      </div>

      <p className="text-foreground text-lg font-semibold">
        कृपया थांबा...
      </p>
      <p className="text-muted-foreground mt-1 text-sm">
        Please wait while we connect you to AgriAlert
      </p>
    </motion.div>
  );
}

/**
 * Call Ended state screen
 */
function CallEndedView({ onRestart }: { onRestart: () => void }) {
  return (
    <motion.div
      key="ended"
      {...VIEW_MOTION_PROPS}
      className="bg-background flex flex-col items-center justify-center px-4 text-center"
    >
      <div className="agri-state-badge agri-state-badge--ended mb-6">
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M8 1C4.13 1 1 4.13 1 8s3.13 7 7 7 7-3.13 7-7-3.13-7-7-7zm3.5 9.5L10 12l-2-2-2 2-1.5-1.5L6.5 8.5l-2-2L6 5l2 2 2-2 1.5 1.5-2 2 2 2z"
            fill="currentColor"
          />
        </svg>
        संवाद संपला / Call Ended
      </div>

      <div className="mb-4 text-5xl" role="img" aria-label="Completed">
        ✅
      </div>

      <h2 className="text-foreground text-xl font-bold md:text-2xl">
        संवाद संपला
      </h2>
      <p className="text-muted-foreground mt-1 text-sm md:text-base">
        Call Ended — Thank you for using AgriAlert!
      </p>

      <Button
        size="lg"
        onClick={onRestart}
        className="mt-8 w-72 rounded-full py-6 text-sm font-bold tracking-wide md:w-80 md:text-base"
      >
        🔄 पुन्हा बोलण्यासाठी क्लिक करा / Start Again
      </Button>

      <p className="text-muted-foreground mt-4 text-xs">
        तुम्ही कधीही पुन्हा AgriAlert शी बोलू शकता
        <br />
        You can talk to AgriAlert again anytime
      </p>
    </motion.div>
  );
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start, end } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const [viewState, setViewState] = useState<AgriViewState>('ready');

  // Track if user has initiated a call
  const handleStart = useCallback(() => {
    setViewState('connecting');
    start();
  }, [start]);

  // Track if user wants to restart
  const handleRestart = useCallback(() => {
    setViewState('ready');
  }, []);

  // Transition from connecting -> active when connected
  useEffect(() => {
    if (isConnected && viewState === 'connecting') {
      setViewState('active');
    }
  }, [isConnected, viewState]);

  // Transition to ended when disconnected after being active
  useEffect(() => {
    if (!isConnected && viewState === 'active') {
      setViewState('ended');
    }
  }, [isConnected, viewState]);

  return (
    <AnimatePresence mode="wait">
      {/* Ready state */}
      {viewState === 'ready' && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
        />
      )}

      {/* Connecting state */}
      {viewState === 'connecting' && !isConnected && (
        <ConnectingView key="connecting" />
      )}

      {/* Active session state (Listening / Speaking handled inside) */}
      {(viewState === 'active' || (viewState === 'connecting' && isConnected)) && isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}

      {/* Call Ended state */}
      {viewState === 'ended' && (
        <CallEndedView key="ended" onRestart={handleRestart} />
      )}
    </AnimatePresence>
  );
}
