import { useState, useCallback } from "react";
import type { ChatMessage, LessonState, LessonItem } from "../types/lesson";
import { sampleLesson } from "../data/sampleLesson";
import ConversationView from "../components/lesson/ConversationView";
import VideoPlayer from "../components/lesson/VideoPlayer";

export default function InteractiveLesson() {
  const [lessonState, setLessonState] = useState<LessonState>(() => {
    const firstItem = sampleLesson[0];
    if (firstItem.type === "conversation") {
      return {
        mode: "conversation",
        itemIndex: 0,
        messages: [{ role: "assistant", content: firstItem.prompt }],
        pendingTransition: false,
      };
    }
    return { mode: "video", itemIndex: 0 };
  });

  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");

  const currentItem: LessonItem | undefined = sampleLesson[
    lessonState.mode === "complete" ? -1 : lessonState.itemIndex
  ];

  const moveToNextItem = useCallback(() => {
    const nextIndex =
      lessonState.mode === "complete" ? 0 : lessonState.itemIndex + 1;
    if (nextIndex >= sampleLesson.length) {
      setLessonState({ mode: "complete" });
      return;
    }

    const nextItem = sampleLesson[nextIndex];
    if (nextItem.type === "conversation") {
      setLessonState({
        mode: "conversation",
        itemIndex: nextIndex,
        messages: [{ role: "assistant", content: nextItem.prompt }],
        pendingTransition: false,
      });
    } else {
      setLessonState({ mode: "video", itemIndex: nextIndex });
    }
  }, [lessonState]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (lessonState.mode !== "conversation") return;

      const userMessage: ChatMessage = { role: "user", content };
      const updatedMessages = [...lessonState.messages, userMessage];

      setLessonState({
        ...lessonState,
        messages: updatedMessages,
        pendingTransition: false,
      });
      setIsLoading(true);
      setStreamingContent("");

      try {
        const currentConvItem = currentItem as { type: "conversation"; prompt: string; systemContext?: string };

        const response = await fetch("/api/chat/lesson", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: updatedMessages,
            system_context: currentConvItem.systemContext,
          }),
        });

        if (!response.ok) throw new Error("Failed to send message");

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let assistantContent = "";
        let shouldTransition = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "text") {
                assistantContent += data.content;
                setStreamingContent(assistantContent);
              } else if (data.type === "tool_use" && data.name === "transition_to_video") {
                shouldTransition = true;
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }

        // Add assistant message
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: assistantContent,
        };

        setLessonState({
          mode: "conversation",
          itemIndex: lessonState.itemIndex,
          messages: [...updatedMessages, assistantMessage],
          pendingTransition: shouldTransition,
        });
      } catch (error) {
        console.error("Error sending message:", error);
        // Add error message
        setLessonState({
          ...lessonState,
          messages: [
            ...updatedMessages,
            { role: "assistant", content: "Sorry, something went wrong. Please try again." },
          ],
          pendingTransition: false,
        });
      } finally {
        setIsLoading(false);
        setStreamingContent("");
      }
    },
    [lessonState, currentItem]
  );

  const handleSkipToVideo = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleConfirmTransition = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleContinueChatting = useCallback(() => {
    if (lessonState.mode === "conversation") {
      setLessonState({ ...lessonState, pendingTransition: false });
    }
  }, [lessonState]);

  const handleVideoEnded = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleVideoSkip = useCallback(() => {
    moveToNextItem();
  }, [moveToNextItem]);

  const handleRestart = useCallback(() => {
    const firstItem = sampleLesson[0];
    if (firstItem.type === "conversation") {
      setLessonState({
        mode: "conversation",
        itemIndex: 0,
        messages: [{ role: "assistant", content: firstItem.prompt }],
        pendingTransition: false,
      });
    } else {
      setLessonState({ mode: "video", itemIndex: 0 });
    }
  }, []);

  // Calculate progress
  const progress =
    lessonState.mode === "complete"
      ? 100
      : Math.round((lessonState.itemIndex / sampleLesson.length) * 100);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Interactive Lesson Prototype
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
        </div>

        {/* Main content */}
        <div className="bg-white rounded-lg shadow-sm p-6 min-h-[500px]">
          {lessonState.mode === "conversation" && (
            <ConversationView
              messages={
                isLoading && streamingContent
                  ? [
                      ...lessonState.messages,
                      { role: "assistant", content: streamingContent },
                    ]
                  : lessonState.messages
              }
              onSendMessage={sendMessage}
              onSkipToVideo={handleSkipToVideo}
              isLoading={isLoading}
              pendingTransition={lessonState.pendingTransition}
              onConfirmTransition={handleConfirmTransition}
              onContinueChatting={handleContinueChatting}
            />
          )}

          {lessonState.mode === "video" && currentItem?.type === "video" && (
            <VideoPlayer
              videoId={currentItem.videoId}
              start={currentItem.start}
              end={currentItem.end}
              onEnded={handleVideoEnded}
              onSkip={handleVideoSkip}
            />
          )}

          {lessonState.mode === "complete" && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Lesson Complete!
              </h2>
              <p className="text-gray-600 mb-6">
                Great work exploring these ideas about AI safety.
              </p>
              <button
                onClick={handleRestart}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                Start Over
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
