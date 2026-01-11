/**
 * Accordion sidebar showing course modules and lessons.
 */

import { useState, useEffect } from "react";
import type { ModuleInfo, LessonInfo } from "../../types/course";
import { ChevronDown, ChevronRight, Check, Circle } from "lucide-react";

type ModuleSidebarProps = {
  courseTitle: string;
  modules: ModuleInfo[];
  selectedLessonId: string | null;
  onLessonSelect: (lesson: LessonInfo) => void;
};

function LessonStatusIcon({ status }: { status: LessonInfo["status"] }) {
  if (status === "completed") {
    return <Check className="w-4 h-4 text-blue-500" />;
  }
  if (status === "in_progress") {
    return <Circle className="w-4 h-4 text-blue-500 fill-blue-500" />;
  }
  return <Circle className="w-4 h-4 text-slate-300" />;
}

export default function ModuleSidebar({
  courseTitle,
  modules,
  selectedLessonId,
  onLessonSelect,
}: ModuleSidebarProps) {
  // Track which modules are expanded
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());

  // Auto-expand module containing selected lesson on mount
  useEffect(() => {
    if (selectedLessonId) {
      for (const module of modules) {
        if (module.lessons.some((l) => l.id === selectedLessonId)) {
          setExpandedModules((prev) => new Set(prev).add(module.id));
          break;
        }
      }
    }
  }, [selectedLessonId, modules]);

  const toggleModule = (moduleId: string) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      if (next.has(moduleId)) {
        next.delete(moduleId);
      } else {
        next.add(moduleId);
      }
      return next;
    });
  };

  const getModuleProgress = (module: ModuleInfo) => {
    const completed = module.lessons.filter((l) => l.status === "completed").length;
    return `${completed}/${module.lessons.length}`;
  };

  return (
    <div className="h-full flex flex-col bg-slate-50 border-r border-slate-200">
      {/* Course title */}
      <div className="p-4 border-b border-slate-200">
        <h1 className="text-lg font-bold text-slate-900">{courseTitle}</h1>
      </div>

      {/* Modules list */}
      <div className="flex-1 overflow-y-auto">
        {modules.map((module) => {
          const isExpanded = expandedModules.has(module.id);

          return (
            <div key={module.id} className="border-b border-slate-200">
              {/* Module header */}
              <button
                onClick={() => toggleModule(module.id)}
                className="w-full flex items-center gap-2 p-4 hover:bg-slate-100 transition-colors text-left"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />
                )}
                <span className="flex-1 font-medium text-slate-900">{module.title}</span>
                <span className="text-sm text-slate-500">{getModuleProgress(module)}</span>
              </button>

              {/* Lessons list */}
              {isExpanded && (
                <div className="pb-2">
                  {module.lessons.map((lesson) => {
                    const isSelected = lesson.id === selectedLessonId;

                    return (
                      <button
                        key={lesson.id}
                        onClick={() => onLessonSelect(lesson)}
                        className={`w-full flex items-center gap-3 px-4 py-2 pl-10 text-left transition-colors ${
                          isSelected
                            ? "bg-blue-50 text-blue-900"
                            : "hover:bg-slate-100 text-slate-700"
                        }`}
                      >
                        <LessonStatusIcon status={lesson.status} />
                        <span className="flex-1 text-sm">{lesson.title}</span>
                        {lesson.status === "in_progress" && (
                          <span className="text-xs text-blue-600 font-medium">Continue</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
