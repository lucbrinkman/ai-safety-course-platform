import { Link } from "react-router-dom";

interface NextLesson {
  slug: string;
  title: string;
}

interface Props {
  isOpen: boolean;
  lessonTitle?: string;
  courseId?: string; // Present when in /course/:courseId/lesson/:lessonId context
  isInSignupsTable?: boolean; // User has signed up for a cohort
  nextLesson?: NextLesson | null; // Next lesson in course, null if last lesson
  completedUnit?: number | null; // Unit number if just completed a unit
  onClose?: () => void; // Called when user clicks outside modal
}

/**
 * Modal shown when a lesson is completed.
 *
 * CTAs are context-aware based on:
 * - Route context (standalone lesson vs course lesson)
 * - Whether user is enrolled in a cohort
 * - Whether there's a next lesson in the course
 */
export default function LessonCompleteModal({
  isOpen,
  lessonTitle,
  courseId,
  isInSignupsTable = false,
  nextLesson,
  completedUnit,
  onClose,
}: Props) {
  if (!isOpen) return null;

  const isInCourseContext = !!courseId;
  const hasNextLesson = !!nextLesson;
  const hasCompletedUnit = completedUnit != null;

  // Determine CTAs based on context
  // Standalone lesson (/lesson/:id):
  //   - Not in signups: "Join Full Course" → /signup, "View Course" → /course
  //   - In signups: "View Course" → /course
  // Course lesson (/course/:id/lesson/:lid):
  //   - Unit complete: "Return to Course" → /course/:id (no secondary CTA)
  //   - Not in signups: "Join Full Course" → /signup, "Return to Course" → /course/:id
  //   - In signups + has next: "Next Lesson" → next lesson URL, "Return to Course" → /course/:id
  //   - In signups + no next: "Return to Course" → /course/:id

  let primaryCta: { label: string; to: string };
  let secondaryCta: { label: string; to: string } | null = null;
  let completionMessage: string;

  if (!isInCourseContext) {
    // Standalone lesson context
    completionMessage = lessonTitle
      ? `You've finished "${lessonTitle}".`
      : "Great work!";
    if (!isInSignupsTable) {
      primaryCta = { label: "Join the Full Course", to: "/signup" };
      secondaryCta = { label: "View Course", to: "/course" };
    } else {
      primaryCta = { label: "View Course", to: "/course" };
    }
  } else {
    // Course lesson context
    const courseUrl = `/course/${courseId}`;

    if (hasCompletedUnit) {
      // Unit completion - show special message, only "Return to Course" button
      completionMessage = `This was the last lesson of Unit ${completedUnit}.`;
      primaryCta = { label: "Return to Course", to: courseUrl };
      // No secondary CTA - don't prompt them to go to next unit yet
    } else if (!isInSignupsTable) {
      completionMessage = lessonTitle
        ? `You've finished "${lessonTitle}".`
        : "Great work!";
      primaryCta = { label: "Join the Full Course", to: "/signup" };
      secondaryCta = { label: "Return to Course", to: courseUrl };
    } else if (hasNextLesson) {
      completionMessage = lessonTitle
        ? `You've finished "${lessonTitle}".`
        : "Great work!";
      const nextLessonUrl = `/course/${courseId}/lesson/${nextLesson!.slug}`;
      primaryCta = { label: `Next: ${nextLesson!.title}`, to: nextLessonUrl };
      secondaryCta = { label: "Return to Course", to: courseUrl };
    } else {
      // End of course
      completionMessage = lessonTitle
        ? `You've finished "${lessonTitle}".`
        : "Great work!";
      primaryCta = { label: "Return to Course", to: courseUrl };
    }
  }

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Only close if clicking the backdrop itself, not the modal content
    if (e.target === e.currentTarget && onClose) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl text-center">
        <div className="text-5xl mb-4">🎉</div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Lesson Complete!
        </h2>
        <p className="text-gray-600 mb-6">
          {completionMessage}{" "}
          {!hasCompletedUnit && "Ready to continue your AI safety journey?"}
        </p>
        <div className="flex flex-col gap-3">
          <Link
            to={primaryCta.to}
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            {primaryCta.label}
          </Link>
          {secondaryCta && (
            <Link
              to={secondaryCta.to}
              className="w-full text-gray-600 py-2 px-4 hover:text-gray-800 transition-colors"
            >
              {secondaryCta.label}
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
