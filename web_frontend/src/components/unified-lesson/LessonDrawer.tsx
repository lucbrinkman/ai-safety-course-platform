/**
 * Slide-out drawer showing lesson overview in the player.
 * Slides in from the right, ~40% width, floats over content.
 */

import { useEffect } from "react";
import { X, List } from "lucide-react";
import type { StageInfo, LessonStatus } from "../../types/course";
import LessonOverview from "../course/LessonOverview";

type LessonDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  lessonTitle: string;
  stages: StageInfo[];
  currentStageIndex: number;
  onStageClick: (index: number) => void;
};

export default function LessonDrawer({
  isOpen,
  onClose,
  lessonTitle,
  stages,
  currentStageIndex,
  onStageClick,
}: LessonDrawerProps) {
  // Close on escape
  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-[40%] max-w-md bg-white shadow-xl z-50 transform transition-transform duration-300 ease-out ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h3 className="text-lg font-medium text-slate-900">Lesson Overview</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 h-[calc(100%-4rem)] overflow-y-auto">
          <LessonOverview
            lessonTitle={lessonTitle}
            stages={stages}
            status="in_progress"
            currentStageIndex={currentStageIndex}
            onStageClick={onStageClick}
            showActions={false}
          />
        </div>
      </div>
    </>
  );
}

/**
 * Button to toggle the drawer, shown in player header.
 */
export function LessonDrawerToggle({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
      title="Lesson Overview"
    >
      <List className="w-5 h-5 text-slate-600" />
    </button>
  );
}
