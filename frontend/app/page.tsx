import { Activity, CloudUpload, GitBranch, RotateCcw } from "lucide-react";

const projects = [
  {
    name: "Azure Core Network",
    environment: "dev",
    status: "Healthy",
    cost: "$63/mo",
    deployments: 14,
  },
  {
    name: "Analytics Storage",
    environment: "stage",
    status: "Needs review",
    cost: "$28/mo",
    deployments: 8,
  },
];

const pipeline = ["Queued", "Validating", "Planning", "Deploying", "Success"];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f6f8fb] text-[#172033]">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-signal">DeployForge</p>
            <h1 className="mt-2 text-3xl font-semibold">Infrastructure deployment control plane</h1>
          </div>
          <button className="inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white shadow-sm">
            <CloudUpload size={18} />
            Upload IaC
          </button>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[1.4fr_0.8fr]">
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["Success rate", "96%", "Last 30 days"],
              ["Resources tracked", "37", "Across dev and stage"],
              ["Estimated spend", "$91/mo", "Simulation only"],
            ].map(([label, value, detail]) => (
              <article key={label} className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-500">{label}</p>
                <p className="mt-3 text-3xl font-semibold">{value}</p>
                <p className="mt-2 text-sm text-slate-500">{detail}</p>
              </article>
            ))}
          </div>

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h2 className="text-lg font-semibold">Projects</h2>
              <span className="text-sm text-slate-500">2 active</span>
            </div>
            <div className="divide-y divide-slate-100">
              {projects.map((project) => (
                <div key={project.name} className="grid gap-4 px-5 py-4 md:grid-cols-[1fr_auto_auto_auto] md:items-center">
                  <div>
                    <h3 className="font-semibold">{project.name}</h3>
                    <p className="text-sm text-slate-500">{project.environment} environment</p>
                  </div>
                  <span className="text-sm font-medium text-signal">{project.status}</span>
                  <span className="text-sm text-slate-600">{project.deployments} deployments</span>
                  <span className="text-sm font-semibold">{project.cost}</span>
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <Activity className="text-signal" />
              <h2 className="text-lg font-semibold">Mock Pipeline</h2>
            </div>
            <div className="mt-5 space-y-3">
              {pipeline.map((stage, index) => (
                <div key={stage} className="flex items-center justify-between rounded-md bg-panel px-4 py-3">
                  <span className="text-sm font-medium">{stage}</span>
                  <span className="text-xs font-semibold text-signal">step {index + 1}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <GitBranch className="text-ink" />
              <h2 className="text-lg font-semibold">Resource Graph</h2>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
              {["resource group", "vnet", "subnet", "vm"].map((item) => (
                <div key={item} className="rounded-md border border-slate-200 bg-panel px-3 py-4 text-center font-medium">
                  {item}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <RotateCcw className="text-danger" />
              <h2 className="text-lg font-semibold">Rollback Ready</h2>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-600">
              Every successful simulated deployment will be versioned so previous infrastructure states can be restored.
            </p>
          </section>
        </aside>
      </section>
    </main>
  );
}
