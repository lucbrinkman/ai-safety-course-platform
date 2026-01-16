"use client";

import { useParams } from "next/navigation";
import UnifiedLesson from "@/pages/UnifiedLesson";

export default function LegacyLessonPage() {
  const params = useParams();
  const lessonId = params.lessonId as string;

  return <UnifiedLesson lessonSlug={lessonId} />;
}
