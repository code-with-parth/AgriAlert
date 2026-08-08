'use client';

import { useCallback, useEffect, useState } from 'react';

export type MicPermissionState = 'prompt' | 'granted' | 'denied' | 'error' | 'checking';

interface UseMicrophonePermissionReturn {
  /** Current mic permission state */
  permissionState: MicPermissionState;
  /** Error message if permission is denied/errored */
  errorMessage: string | null;
  /** Re-check permission (e.g. after user changes browser settings) */
  recheckPermission: () => void;
  /** Dismiss the error banner */
  dismissError: () => void;
}

export function useMicrophonePermission(): UseMicrophonePermissionReturn {
  const [permissionState, setPermissionState] = useState<MicPermissionState>('checking');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const checkPermission = useCallback(async () => {
    setDismissed(false);

    try {
      // Try the Permissions API first (supported in Chrome/Edge)
      if (navigator.permissions && navigator.permissions.query) {
        try {
          const result = await navigator.permissions.query({
            name: 'microphone' as PermissionName,
          });

          if (result.state === 'denied') {
            setPermissionState('denied');
            setErrorMessage(
              '⚠️ मायक्रोफोन परवानगी नाकारली / Microphone access blocked. Please allow mic access in your browser settings to talk to AgriAlert.'
            );
            return;
          }

          if (result.state === 'granted') {
            setPermissionState('granted');
            setErrorMessage(null);
            return;
          }

          // 'prompt' — user hasn't decided yet, that's fine
          setPermissionState('prompt');
          setErrorMessage(null);

          // Listen for changes
          result.addEventListener('change', () => {
            if (result.state === 'denied') {
              setPermissionState('denied');
              setErrorMessage(
                '⚠️ मायक्रोफोन परवानगी नाकारली / Microphone access blocked. Please allow mic access in your browser settings to talk to AgriAlert.'
              );
            } else if (result.state === 'granted') {
              setPermissionState('granted');
              setErrorMessage(null);
            }
          });

          return;
        } catch {
          // Permissions API not supported for microphone in this browser — fall through
        }
      }

      // Fallback: try getUserMedia to check
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          // Successfully got access — clean up
          stream.getTracks().forEach((track) => track.stop());
          setPermissionState('granted');
          setErrorMessage(null);
        } catch (err) {
          const error = err as DOMException;
          if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            setPermissionState('denied');
            setErrorMessage(
              '⚠️ मायक्रोफोन परवानगी नाकारली / Microphone access blocked. Please allow mic access in your browser settings to talk to AgriAlert.'
            );
          } else if (error.name === 'NotFoundError') {
            setPermissionState('error');
            setErrorMessage(
              '⚠️ मायक्रोफोन सापडला नाही / No microphone found. Please connect a microphone to talk to AgriAlert.'
            );
          } else {
            setPermissionState('error');
            setErrorMessage(
              `⚠️ मायक्रोफोन त्रुटी / Microphone error: ${error.message}`
            );
          }
        }
      } else {
        // No mediaDevices API — possibly insecure context
        setPermissionState('error');
        setErrorMessage(
          '⚠️ तुमचा ब्राउझर मायक्रोफोन सपोर्ट करत नाही / Your browser does not support microphone access. Please use a modern browser.'
        );
      }
    } catch {
      setPermissionState('error');
      setErrorMessage(
        '⚠️ मायक्रोफोन तपासताना त्रुटी / Error checking microphone permission.'
      );
    }
  }, []);

  useEffect(() => {
    checkPermission();
  }, [checkPermission]);

  return {
    permissionState,
    errorMessage: dismissed ? null : errorMessage,
    recheckPermission: checkPermission,
    dismissError: () => setDismissed(true),
  };
}
