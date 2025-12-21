import { useEffect, useRef, useState } from "react";
import "youtube-video-element";
import {
  MediaController,
  MediaControlBar,
  MediaPlayButton,
  MediaMuteButton,
  MediaVolumeRange,
  MediaFullscreenButton,
} from "media-chrome/react";

type VideoPlayerProps = {
  videoId: string;
  start: number;
  end: number;
  onEnded: () => void;
  onSkip: () => void;
};

// Extend JSX to include the youtube-video custom element
declare global {
  namespace JSX {
    interface IntrinsicElements {
      "youtube-video": React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          src?: string;
          autoplay?: boolean;
          muted?: boolean;
        },
        HTMLElement
      >;
    }
  }
}

export default function VideoPlayer({
  videoId,
  start,
  end,
  onEnded,
  onSkip,
}: VideoPlayerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hasEndedRef = useRef(false);
  const [progress, setProgress] = useState(0);
  const [fragmentEnded, setFragmentEnded] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const progressBarRef = useRef<HTMLDivElement | null>(null);

  const duration = end - start;
  const youtubeUrl = `https://www.youtube.com/watch?v=${videoId}&t=${start}`;

  // Get video element reference from container (scoped query, not global)
  useEffect(() => {
    if (!containerRef.current) return;

    const video = containerRef.current.querySelector("youtube-video") as HTMLVideoElement | null;
    if (!video) return;

    videoRef.current = video;

    const handleLoadedMetadata = () => {
      video.currentTime = start;
      video.play();
    };

    const handleTimeUpdate = () => {
      if (hasEndedRef.current) return;

      const currentTime = video.currentTime;

      // If user seeks before fragment start, snap back
      if (currentTime < start - 0.5) {
        video.currentTime = start;
        return;
      }

      const elapsed = Math.max(0, currentTime - start);
      setProgress(Math.min(elapsed / duration, 1));

      if (currentTime >= end) {
        hasEndedRef.current = true;
        video.pause();
        setProgress(1);
        setFragmentEnded(true);
      }
    };

    video.addEventListener("loadedmetadata", handleLoadedMetadata);
    video.addEventListener("timeupdate", handleTimeUpdate);

    return () => {
      video.removeEventListener("loadedmetadata", handleLoadedMetadata);
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [start, end, duration]);

  const handleReplay = () => {
    const video = videoRef.current;
    if (video) {
      hasEndedRef.current = false;
      setFragmentEnded(false);
      setProgress(0);
      video.currentTime = start;
      video.play();
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const seekToPosition = (clientX: number) => {
    if (!progressBarRef.current || !videoRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percentage = clickX / rect.width;
    const newTime = start + percentage * duration;
    videoRef.current.currentTime = newTime;
    setProgress(percentage);
    if (hasEndedRef.current && percentage < 1) {
      hasEndedRef.current = false;
      setFragmentEnded(false);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    seekToPosition(e.clientX);
  };

  // Handle drag and release globally
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      seekToPosition(e.clientX);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, start, duration]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div
        ref={containerRef}
        className="w-full max-w-3xl aspect-video relative"
      >
        <MediaController className="w-full h-full">
          <youtube-video
            slot="media"
            src={youtubeUrl}
            autoplay
          />
          <MediaControlBar>
            <MediaPlayButton />
            <MediaMuteButton />
            <MediaVolumeRange />
            {/* Custom fragment progress bar */}
            <div
              ref={progressBarRef}
              className="flex-1 rounded cursor-pointer relative select-none mx-2 self-center"
              style={{ height: "4px", backgroundColor: "#444" }}
              onMouseDown={handleMouseDown}
            >
              <div
                className="h-full rounded pointer-events-none"
                style={{ width: `${progress * 100}%`, backgroundColor: "#888" }}
              />
              <div
                className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full shadow pointer-events-none"
                style={{ left: `calc(${progress * 100}% - 6px)`, backgroundColor: "#888" }}
              />
            </div>
            <span style={{ color: "#888", fontSize: "12px", marginLeft: "8px", marginRight: "8px", whiteSpace: "nowrap", alignSelf: "center" }}>
              {formatTime(progress * duration)} / {formatTime(duration)}
            </span>
            <MediaFullscreenButton />
          </MediaControlBar>
        </MediaController>
        {/* Overlay to dim YouTube branding */}
        <div
          className="absolute bottom-0 right-0 pointer-events-none"
          style={{
            width: "120px",
            height: "40px",
            background: "linear-gradient(to right, transparent, rgba(0,0,0,0.7))",
          }}
        />
      </div>

      {/* Clip info - always visible */}
      <div className="text-center text-xs text-gray-400">
        {duration}s clip from {formatTime(start)} – {formatTime(end)}
      </div>


      {fragmentEnded ? (
        <div className="flex gap-4">
          <button
            onClick={handleReplay}
            className="border border-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-50"
          >
            Replay
          </button>
          <button
            onClick={onEnded}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Continue to next question
          </button>
        </div>
      ) : (
        <button
          onClick={onSkip}
          className="text-gray-500 hover:text-gray-700 text-sm underline"
        >
          Skip to next question
        </button>
      )}
    </div>
  );
}
