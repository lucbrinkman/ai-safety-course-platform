import type { AvailabilityData } from "../../types/signup";
import ScheduleSelector from "../schedule/ScheduleSelector";

interface AvailabilityStepProps {
  availability: AvailabilityData;
  onAvailabilityChange: (data: AvailabilityData) => void;
  onBack: () => void;
  onSubmit: () => void;
}

export default function AvailabilityStep({
  availability,
  onAvailabilityChange,
  onBack,
  onSubmit,
}: AvailabilityStepProps) {
  const totalSlots = Object.values(availability).reduce(
    (sum, slots) => sum + slots.length,
    0,
  );

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Your Availability
      </h2>
      <p className="text-gray-600 mb-6">
        Select the times when you're available to participate in course
        sessions. This helps us match you with a group that fits your schedule.
      </p>

      <ScheduleSelector
        value={availability}
        onChange={onAvailabilityChange}
        startHour={8}
        endHour={22}
      />

      <div className="mt-8 flex gap-4">
        <button
          type="button"
          onClick={onBack}
          className="px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          type="button"
          onClick={onSubmit}
          disabled={totalSlots === 0}
          className={`flex-1 px-6 py-3 font-medium rounded-lg transition-colors ${
            totalSlots === 0
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-blue-500 hover:bg-blue-600 text-white"
          }`}
        >
          {totalSlots === 0
            ? "Select at least one time slot"
            : "Complete Signup"}
        </button>
      </div>
    </div>
  );
}
