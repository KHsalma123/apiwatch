import { useNavigate, useParams } from "react-router-dom";
import { ErrorBanner, Loading } from "../components/Feedback";
import MonitorForm from "../components/MonitorForm";
import { panel } from "../components/ui";
import { useFetch } from "../hooks/useFetch";
import { monitorsApi } from "../services/apiwatch";

/** Used for both "Add monitor" (/monitors/new) and "Edit monitor" (/monitors/:id/edit). */
export default function MonitorFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const editing = Boolean(id);
  const { data, error, loading, reload } = useFetch(() => (editing ? monitorsApi.get(id) : Promise.resolve(null)), [id]);

  if (loading) return <Loading />;
  if (error) return <ErrorBanner message={error} onRetry={reload} />;

  async function submit(body) {
    const saved = editing ? await monitorsApi.update(id, body) : await monitorsApi.create(body);
    navigate(`/monitors/${saved.id}`);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-semibold">{editing ? "Edit monitor" : "Add a monitor"}</h1>
      <div className={`${panel} p-6`}>
        <MonitorForm
          initial={data}
          submitLabel={editing ? "Save changes" : "Add monitor"}
          onSubmit={submit}
          onCancel={() => navigate(editing ? `/monitors/${id}` : "/monitors")}
        />
      </div>
    </div>
  );
}
