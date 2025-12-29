import { Routes, Route } from "react-router";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import Availability from "./pages/Availability";
import Auth from "./pages/Auth";
import NotFound from "./pages/NotFound";
import InteractiveLesson from "./pages/InteractiveLesson";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/availability" element={<Availability />} />
        <Route path="/auth/code" element={<Auth />} />
        <Route path="/prototype/interactive-lesson" element={<InteractiveLesson />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default App;
