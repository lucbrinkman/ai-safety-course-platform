// web_frontend/src/components/unified-lesson/ContentPanel.tsx
import { useState, useCallback, useEffect } from "react";
import {
  useFloating,
  useClick,
  useDismiss,
  useInteractions,
  offset,
  flip,
  shift,
  FloatingPortal,
} from "@floating-ui/react";
import type { Stage, PreviousStageInfo, ArticleData } from "../../types/unified-lesson";
import ArticlePanel from "./ArticlePanel";
import VideoPlayer from "./VideoPlayer";
import OptionalBanner from "./OptionalBanner";

type ContentPanelProps = {
  stage: Stage | null;
  article?: ArticleData | null;
  onVideoEnded: () => void;
  onNextClick: () => void;
  onSkipOptional?: () => void;
  isReviewing?: boolean;
  isPreviewing?: boolean;  // Viewing future stage
  // For chat stages: show previous content (blurred or visible)
  previousArticle?: ArticleData | null;
  previousStage?: PreviousStageInfo | null;
  showUserPreviousContent?: boolean;
};

export default function ContentPanel({
  stage,
  article,
  onVideoEnded,
  onNextClick,
  onSkipOptional,
  isReviewing = false,
  isPreviewing = false,
  previousArticle,
  previousStage,
  showUserPreviousContent = true,
}: ContentPanelProps) {
  // Track if user has scrolled to bottom of article
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);
  const handleScrolledToBottom = useCallback(() => {
    setHasScrolledToBottom(true);
  }, []);

  // Track if article content fits without scrolling
  const [contentFits, setContentFits] = useState<boolean | null>(null);
  const handleContentFitsChange = useCallback((fits: boolean) => {
    setContentFits(fits);
  }, []);

  // Reset contentFits when article changes
  useEffect(() => {
    setContentFits(null);
  }, [article?.content]);

  // Popover for "haven't scrolled yet" confirmation
  const [skipPopoverOpen, setSkipPopoverOpen] = useState(false);
  const { refs, floatingStyles, context } = useFloating({
    open: skipPopoverOpen,
    onOpenChange: setSkipPopoverOpen,
    placement: "top",
    middleware: [offset(8), flip(), shift({ padding: 8 })],
  });
  const click = useClick(context);
  const dismiss = useDismiss(context);
  const { getReferenceProps, getFloatingProps } = useInteractions([click, dismiss]);

  const handleReadButtonClick = () => {
    if (hasScrolledToBottom) {
      onNextClick();
    }
    // If not scrolled, the popover opens via useClick
  };

  // Determine what article to show (if any) and how to show it
  const isArticleStage = stage?.type === "article";
  const isChatAfterArticle = stage?.type === "chat" && previousStage?.type === "article" && !!previousArticle;
  const shouldShowArticle = isArticleStage || isChatAfterArticle;

  // Unified article data: current article for article stage, previous for chat stage
  const articleToShow = isArticleStage ? (article ?? { content: "Loading..." }) : previousArticle;
  const isBlurred = isChatAfterArticle && !showUserPreviousContent;
  const showButton = isArticleStage && !isReviewing;

  if (!stage) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <p className="text-gray-500">Lesson complete!</p>
      </div>
    );
  }

  // Unified article rendering - same JSX position for both article and chat-after-article
  if (shouldShowArticle && articleToShow) {
    const isOptional = stage && 'optional' in stage && stage.optional === true;
    const showOptionalBanner = isOptional && !isReviewing && !isPreviewing && onSkipOptional;

    // Button component (reused for inline and sticky)
    const buttonElement = showButton && (
      <>
        <button
          ref={hasScrolledToBottom ? undefined : refs.setReference}
          onClick={handleReadButtonClick}
          {...(hasScrolledToBottom ? {} : getReferenceProps())}
          className="w-full py-2 rounded-lg bg-gray-300 text-black hover:bg-gray-400"
          data-testid="done-reading-button"
        >
          Done reading
        </button>
        {skipPopoverOpen && !hasScrolledToBottom && (
          <FloatingPortal>
            <div
              ref={refs.setFloating}
              style={floatingStyles}
              {...getFloatingProps()}
              className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50 max-w-xs"
            >
              <p className="text-sm text-gray-700 mb-3">
                It looks like you haven't reached the bottom of the article yet. What would you like to do?
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setSkipPopoverOpen(false);
                    onNextClick();
                  }}
                  className="flex-1 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Skip anyway
                </button>
                <button
                  onClick={() => setSkipPopoverOpen(false)}
                  className="flex-1 px-3 py-1.5 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded"
                >
                  Keep reading
                </button>
              </div>
            </div>
          </FloatingPortal>
        )}
      </>
    );

    // Short article: button inline after content
    // Long article (or unknown): button in sticky footer
    const useInlineButton = contentFits === true;
    const useStickyFooter = contentFits !== true;  // Show sticky for false or null (unknown)

    const afterContent = showButton && useInlineButton ? (
      <div className="max-w-[620px] mx-auto px-6 pb-6">
        {buttonElement}
      </div>
    ) : undefined;

    // Should we show the button in the sticky footer (vs inline after content)?
    const showButtonInFooter = showButton && useStickyFooter;

    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-hidden">
          {showOptionalBanner && (
            <div className="px-4 pt-4 max-w-[620px] mx-auto">
              <OptionalBanner stageType="article" onSkip={onSkipOptional} />
            </div>
          )}
          <ArticlePanel
            article={articleToShow}
            blurred={isBlurred}
            onScrolledToBottom={showButton ? handleScrolledToBottom : undefined}
            onContentFitsChange={showButton ? handleContentFitsChange : undefined}
            afterContent={afterContent}
          />
        </div>
        {/* Always reserve footer space to prevent layout shift between article and chat stages */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="max-w-[620px] mx-auto">
            {showButtonInFooter ? (
              buttonElement
            ) : (
              /* Invisible placeholder to maintain layout */
              <div className="py-2 invisible">Placeholder</div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Chat stage with video as previous content
  if (stage.type === "chat" && previousStage?.type === "video" && previousStage.videoId) {
    const blurred = !showUserPreviousContent;

    // When showing: display actual video player
    // When blurred: display thumbnail with blur overlay
    if (!blurred) {
      return (
        <div className="h-full flex flex-col justify-center">
          <VideoPlayer
            videoId={previousStage.videoId}
            start={previousStage.from ?? 0}
            end={previousStage.to ?? 9999}
            onEnded={() => {}}
            hideControls
          />
        </div>
      );
    }

    const thumbnailUrl = `https://img.youtube.com/vi/${previousStage.videoId}/maxresdefault.jpg`;
    return (
      <div className="h-full flex items-center justify-center bg-white overflow-hidden relative">
        <img
          src={thumbnailUrl}
          alt="Video thumbnail"
          className="max-w-full max-h-full object-contain blur-sm"
        />
        <div className="absolute inset-0 flex items-center justify-center z-20">
          <div className="bg-white rounded-lg px-6 py-4 shadow-lg text-center">
            <svg className="w-8 h-8 mx-auto mb-2 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
            </svg>
            <p className="text-gray-600 text-sm">Please chat with the AI tutor</p>
          </div>
        </div>
      </div>
    );
  }

  // Chat stage fallback (no previous content)
  if (stage.type === "chat") {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 p-8">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">💬</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Discussion Time</h2>
          <p className="text-gray-600">
            Use the chat on the left to discuss what you've learned.
          </p>
        </div>
      </div>
    );
  }

  // Video stage
  if (stage.type === "video") {
    const isOptional = 'optional' in stage && stage.optional === true;
    const showOptionalBanner = isOptional && !isReviewing && !isPreviewing && onSkipOptional;
    const showDoneWatching = !isReviewing && !isPreviewing;

    return (
      <div className="h-full flex flex-col">
        {showOptionalBanner && (
          <div className="px-4 pt-4 max-w-[620px] mx-auto">
            <OptionalBanner stageType="video" onSkip={onSkipOptional} />
          </div>
        )}
        <div className="flex-1 flex flex-col justify-center">
          <VideoPlayer
            videoId={stage.videoId}
            start={stage.from}
            end={stage.to || 9999}
            onEnded={isReviewing ? () => {} : onVideoEnded}
          />
        </div>
        {/* Always reserve footer space to prevent layout shift between stages */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="max-w-[620px] mx-auto">
            {showDoneWatching ? (
              <button
                onClick={onNextClick}
                className="w-full py-2 rounded-lg bg-gray-300 text-black hover:bg-gray-400"
              >
                Done watching
              </button>
            ) : (
              /* Invisible placeholder to maintain layout */
              <div className="py-2 invisible">Placeholder</div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
}
