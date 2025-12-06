import { useState } from "react";
import type { SignupFormData } from "../../types/signup";
import { EMPTY_AVAILABILITY, getBrowserTimezone } from "../../types/signup";
import PersonalInfoStep from "./PersonalInfoStep";
import AvailabilityStep from "./AvailabilityStep";
import SuccessMessage from "./SuccessMessage";

type Step = 1 | 2 | "complete";

export default function SignupWizard() {
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [formData, setFormData] = useState<SignupFormData>({
    firstName: "",
    lastName: "",
    discordConnected: false,
    discordUsername: undefined,
    availability: { ...EMPTY_AVAILABILITY },
    timezone: getBrowserTimezone(),
  });

  const handleDiscordConnect = () => {
    // Mock Discord OAuth - in production this would redirect to Discord
    setTimeout(() => {
      setFormData((prev) => ({
        ...prev,
        discordConnected: true,
        discordUsername: "MockUser#1234",
      }));
    }, 500);
  };

  const handleSubmit = () => {
    // Mock submission - log to console
    console.log("Form submitted:", formData);
    setCurrentStep("complete");
  };

  if (currentStep === "complete") {
    return <SuccessMessage formData={formData} />;
  }

  return (
    <div>
      {currentStep === 1 && (
        <PersonalInfoStep
          firstName={formData.firstName}
          lastName={formData.lastName}
          discordConnected={formData.discordConnected}
          discordUsername={formData.discordUsername}
          onFirstNameChange={(value) =>
            setFormData((prev) => ({ ...prev, firstName: value }))
          }
          onLastNameChange={(value) =>
            setFormData((prev) => ({ ...prev, lastName: value }))
          }
          onDiscordConnect={handleDiscordConnect}
          onNext={() => setCurrentStep(2)}
        />
      )}

      {currentStep === 2 && (
        <AvailabilityStep
          availability={formData.availability}
          onAvailabilityChange={(data) =>
            setFormData((prev) => ({ ...prev, availability: data }))
          }
          timezone={formData.timezone}
          onTimezoneChange={(tz) =>
            setFormData((prev) => ({ ...prev, timezone: tz }))
          }
          onBack={() => setCurrentStep(1)}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  );
}
