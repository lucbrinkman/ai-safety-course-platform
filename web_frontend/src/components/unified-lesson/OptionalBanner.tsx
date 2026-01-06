// web_frontend/src/components/unified-lesson/OptionalBanner.tsx

type OptionalBannerProps = {
  onSkip: () => void;
};

export default function OptionalBanner({ onSkip }: OptionalBannerProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <svg
          className="w-4 h-4 text-blue-500 flex-shrink-0"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
            clipRule="evenodd"
          />
        </svg>
        <span className="text-sm text-blue-700">This reading is optional.</span>
      </div>
      <button
        onClick={onSkip}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium whitespace-nowrap"
      >
        Skip to next →
      </button>
    </div>
  );
}
