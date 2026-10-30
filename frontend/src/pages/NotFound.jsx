import { Link } from "react-router-dom";
import { btn } from "../components/ui";

export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="mt-2 text-ink-600">The page you are looking for does not exist or was moved.</p>
      <Link to="/" className={`${btn.primary} mt-6`}>Go to the dashboard</Link>
    </div>
  );
}
