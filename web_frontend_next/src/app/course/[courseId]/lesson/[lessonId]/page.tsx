"use client";

import { useParams } from "next/navigation";
import UnifiedLesson from "@/pages/UnifiedLesson";

export default function LessonPage() {
  const params = useParams();
  const courseId = params.courseId as string;
  const lessonId = params.lessonId as string;

  return <UnifiedLesson courseId={courseId} lessonSlug={lessonId} />;
}
