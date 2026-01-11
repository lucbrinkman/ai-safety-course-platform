/**
 * Types for course overview feature.
 */

export type StageInfo = {
  type: "article" | "video" | "chat";
  title: string;
  duration: string | null;
  optional: boolean;
};

export type LessonStatus = "completed" | "in_progress" | "not_started";

export type LessonInfo = {
  id: string;
  title: string;
  stages: StageInfo[];
  status: LessonStatus;
  currentStageIndex: number | null;
  sessionId: number | null;
};

export type ModuleInfo = {
  id: string;
  title: string;
  lessons: LessonInfo[];
};

export type CourseProgress = {
  course: {
    id: string;
    title: string;
  };
  modules: ModuleInfo[];
};
