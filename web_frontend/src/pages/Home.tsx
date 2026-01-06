import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="py-16 max-w-2xl mx-auto text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        AI Safety Course Platform
      </h1>
      <p className="text-xl text-gray-600 mb-8">
        Learn about AI safety and alignment through interactive lessons.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link
          to="/lesson/intelligence-feedback-loop"
          className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
        >
          Start Learning
        </Link>
        <Link
          to="/signup"
          className="bg-white text-indigo-600 border-2 border-indigo-600 px-8 py-3 rounded-lg font-medium hover:bg-indigo-50 transition-colors"
        >
          Sign Up
        </Link>
      </div>

      <p className="text-sm text-gray-500 mt-6">
        Try our intro lesson first, or sign up directly for the full course.
      </p>
    </div>
  );
}
