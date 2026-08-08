import { Button } from '@/components/ui/button';

function AgriIcon() {
  return (
    <svg
      width="80"
      height="80"
      viewBox="0 0 80 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-4 size-20"
    >
      {/* Sprout / seedling icon */}
      <circle cx="40" cy="40" r="38" fill="currentColor" opacity="0.08" />
      <circle cx="40" cy="40" r="28" fill="currentColor" opacity="0.06" />
      {/* Stem */}
      <path
        d="M40 58V35"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
      {/* Left leaf */}
      <path
        d="M40 42C36 42 28 38 26 28C30 28 38 30 40 42Z"
        fill="currentColor"
        opacity="0.7"
      />
      {/* Right leaf */}
      <path
        d="M40 35C44 35 52 30 54 20C50 20 42 23 40 35Z"
        fill="currentColor"
        opacity="0.85"
      />
      {/* Small leaf */}
      <path
        d="M40 48C37 48 32 46 31 40C34 40 38 42 40 48Z"
        fill="currentColor"
        opacity="0.5"
      />
      {/* Ground dots */}
      <ellipse cx="40" cy="60" rx="12" ry="2" fill="currentColor" opacity="0.15" />
    </svg>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref}>
      <section className="bg-background flex flex-col items-center justify-center px-4 text-center">
        {/* Ready state badge */}
        <div className="agri-state-badge agri-state-badge--ready mb-6">
          <span className="inline-block size-2 animate-pulse rounded-full bg-current" />
          तयार / Ready
        </div>

        <AgriIcon />

        <h1 className="text-foreground text-2xl font-bold tracking-tight md:text-3xl">
          AgriAlert{' '}
          <span className="text-primary text-xl md:text-2xl">(कृषीअलर्ट)</span>
        </h1>

        <p className="text-muted-foreground mt-2 max-w-prose text-sm leading-6 md:text-base">
          तुमचा डिजिटल शेती मित्र — Your Digital Farming Companion
        </p>

        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-8 w-72 rounded-full py-6 text-sm font-bold tracking-wide md:w-80 md:text-base"
        >
          {startButtonText}
        </Button>

        <p className="text-muted-foreground mt-4 max-w-xs text-xs leading-5 md:max-w-sm md:text-sm">
          बोलण्यासाठी बटण दाबा आणि तुमचा प्रश्न विचारा
          <br />
          Press the button and ask your question
        </p>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center px-4">
        <p className="text-muted-foreground max-w-prose pt-1 text-center text-xs leading-5 font-normal text-pretty">
          मदतीसाठी{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://murf.ai/api/docs/text-to-speech/streaming"
            className="underline"
          >
            Murf Falcon TTS Docs
          </a>{' '}
          पहा | See{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="underline"
          >
            Voice AI Quickstart
          </a>
        </p>
      </div>
    </div>
  );
};
