import { useEffect, useState, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router";

const API_URL = import.meta.env.VITE_API_URL ?? "";

type AuthStatus = "loading" | "success" | "error";

export default function Auth() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const hasValidated = useRef(false);

  const code = searchParams.get("code");
  const next = searchParams.get("next") || "/signup";

  useEffect(() => {
    // Prevent double validation (React strict mode runs effects twice)
    if (hasValidated.current) return;
    hasValidated.current = true;

    if (!code) {
      setStatus("error");
      setErrorMessage("No authentication code provided.");
      return;
    }

    // Validate code via API
    const origin = encodeURIComponent(window.location.origin);
    fetch(`${API_URL}/auth/code?code=${encodeURIComponent(code)}&next=${encodeURIComponent(next)}&origin=${origin}`, {
      method: "POST",
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          setStatus("success");
          // Small delay to show success message, then navigate
          setTimeout(() => {
            navigate(data.next || next);
          }, 500);
        } else {
          setStatus("error");
          switch (data.error) {
            case "expired_code":
              setErrorMessage("This link has expired. Please request a new one or sign in with Discord.");
              break;
            case "invalid_code":
              setErrorMessage("This link is invalid or has already been used.");
              break;
            default:
              setErrorMessage("Authentication failed. Please try again.");
          }
        }
      })
      .catch((err) => {
        console.error("Auth error:", err);
        setStatus("error");
        setErrorMessage("Unable to connect to the server. Please try again.");
      });
  }, [code, next, navigate]);

  const handleDiscordLogin = () => {
    const origin = encodeURIComponent(window.location.origin);
    window.location.href = `${API_URL}/auth/discord?next=${encodeURIComponent(next)}&origin=${origin}`;
  };

  if (status === "loading") {
    return (
      <div className="py-16 text-center">
        <div className="max-w-md mx-auto">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Authenticating...</p>
        </div>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="py-16 text-center">
        <div className="max-w-md mx-auto">
          <div className="text-green-500 text-5xl mb-4">✓</div>
          <p className="text-lg text-gray-600">Success! Redirecting...</p>
        </div>
      </div>
    );
  }

  // Error state
  return (
    <div className="py-16 text-center">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
        <div className="text-red-500 text-5xl mb-4">!</div>
        <h1 className="text-xl font-semibold text-gray-800 mb-2">
          Authentication Failed
        </h1>
        <p className="text-gray-600 mb-6">{errorMessage}</p>
        <button
          onClick={handleDiscordLogin}
          className="inline-flex items-center gap-2 px-6 py-3 bg-[#5865F2] text-white rounded-lg hover:bg-[#4752C4] transition-colors font-medium"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
          </svg>
          Sign in with Discord
        </button>
      </div>
    </div>
  );
}
