/**
 * Types for interactive lesson feature.
 */

export type ConversationItem = {
  type: "conversation";
  prompt: string;
  systemContext?: string;
};

export type VideoItem = {
  type: "video";
  videoId: string;
  start: number; // seconds
  end: number; // seconds
};

export type LessonItem = ConversationItem | VideoItem;

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type LessonState =
  | { mode: "conversation"; itemIndex: number; messages: ChatMessage[]; pendingTransition: boolean }
  | { mode: "video"; itemIndex: number }
  | { mode: "complete" };
