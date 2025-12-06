export type DayName =
  | "Monday"
  | "Tuesday"
  | "Wednesday"
  | "Thursday"
  | "Friday"
  | "Saturday"
  | "Sunday";

export type TimeSlot = string; // "09:00", "14:00", etc.

export type AvailabilityData = Record<DayName, TimeSlot[]>;

export interface SignupFormData {
  firstName: string;
  lastName: string;
  discordConnected: boolean;
  discordUsername?: string;
  availability: AvailabilityData;
}

export const DAY_NAMES: DayName[] = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export const EMPTY_AVAILABILITY: AvailabilityData = {
  Monday: [],
  Tuesday: [],
  Wednesday: [],
  Thursday: [],
  Friday: [],
  Saturday: [],
  Sunday: [],
};

export function formatTimeSlot(slot: number): TimeSlot {
  const hour = Math.floor(slot);
  const minutes = slot % 1 >= 0.5 ? "30" : "00";
  return `${hour.toString().padStart(2, "0")}:${minutes}`;
}
