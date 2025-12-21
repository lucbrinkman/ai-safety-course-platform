import type { LessonItem } from "../types/lesson";

/**
 * Sample lesson for testing the interactive lesson prototype.
 * Uses a real AI safety video with relevant timestamps.
 */
export const sampleLesson: LessonItem[] = [
  {
    type: "conversation",
    prompt: "Do you think AGI — artificial general intelligence — is possible?",
    systemContext:
      "This is the opening question. Get the user to commit to a position, then probe their reasoning. If they say yes, ask how they would respond to someone who says it's impossible. If they say no, ask them to explain why.",
  },
  {
    type: "video",
    // Robert Miles - "Why AI Safety?" (5 second fragment starting at 3:57)
    videoId: "pYXy-A4siMw",
    start: 237,
    end: 242,
  },
  {
    type: "conversation",
    prompt: "What stood out to you from that segment?",
    systemContext:
      "This is a reflection question after the first video segment. Help them connect what they just watched to their earlier thinking. Ask what surprised them or challenged their assumptions.",
  },
  {
    type: "video",
    // Robert Miles - "Why AI Safety?" (5 second fragment starting at 5:30)
    videoId: "pYXy-A4siMw",
    start: 330,
    end: 335,
  },
  {
    type: "conversation",
    prompt: "Based on what you've seen so far, what do you think are the main challenges in ensuring AI systems are safe?",
    systemContext:
      "Final reflection. Help them synthesize their learning. If their answer is shallow, probe deeper. If they mention alignment, ask them to elaborate on what that means.",
  },
];
