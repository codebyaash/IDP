"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { Activity, CloudUpload, FileCode2, GitBranch, ListChecks, Play, Plus, RotateCcw } from "lucide-react";

import {
  createProject,
  deployTemplate,
  fetchDeployments,
  fetchProjects,
  planTemplate,
  type Deployment,
  type DeploymentPlan,
  type Project,
  type TemplateUploadResult,
  uploadTemplate,
} from "@/lib/api";

const fallbackProjects: Project[] = [
  {
    id: "demo-azure-core",
    name: "Azure Core Network",
    cloud_provider: "azure",
    environment: "dev",
    status: "healthy",
    monthly_cost: 63,
    created_at: new Date().toISOString(),
  },
];

const pipeline = ["Queued", "Validating", "Planning", "Deploying", "Success"];

export function ProjectDashboard() {
  const [projects, setProjects] = useState<Project[]>(fallbackProjects);
  const [name, setName] = useState("");
  const [environment, setEnvironment] = useState("dev");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState(fallbackProjects[0].id);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<TemplateUploadResult | null>(null);
  const [deploymentPlan, setDeploymentPlan] = useState<DeploymentPlan | null>(null);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [latestDeployment, setLatestDeployment] = useState<Deployment | null>(null);
  const [isDeploying, setIsDeploying] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchProjects()
      .then((data) => {
        setProjects(data);
        setSelectedProjectId((current) => current || data[0]?.id || "");
        setError("");
      })
      .catch(() => {
        setError("API unavailable. Showing demo data.");
      })
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedProjectId) {
      return;
    }

    fetchDeployments(selectedProjectId)
      .then((data) => {
        setDeployments(data);
        setLatestDeployment(data[0] ?? null);
      })
      .catch(() => {
        setDeployments([]);
      });
  }, [selectedProjectId]);

  const totalCost = useMemo(() => projects.reduce((sum, project) => sum + project.monthly_cost, 0), [projects]);
  const deploymentCount = projects.length * 7;

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }

    setIsCreating(true);
    try {
      const project = await createProject({
        name: name.trim(),
        cloud_provider: "azure",
        environment,
      });
      setProjects((current) => [project, ...current]);
      setSelectedProjectId(project.id);
      setName("");
      setError("");
    } catch {
      setError("Could not create project. Check that the API server is running.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleUploadTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProjectId || !selectedFile) {
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadTemplate(selectedProjectId, selectedFile);
      const plan = await planTemplate(result.template.id);
      setUploadResult(result);
      setDeploymentPlan(plan);
      setSelectedFile(null);
      setError("");
    } catch {
      setError("Could not upload template. Confirm the file has supported IaC syntax.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDeployTemplate() {
    if (!uploadResult) {
      return;
    }

    setIsDeploying(true);
    try {
      const deployment = await deployTemplate(uploadResult.template.id);
      setLatestDeployment(deployment);
      setDeployments((current) => [deployment, ...current.filter((item) => item.id !== deployment.id)]);
      setError("");
    } catch {
      setError("Could not run deployment simulation for this template.");
    } finally {
      setIsDeploying(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f6f8fb] text-[#172033]">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-signal">DeployForge</p>
            <h1 className="mt-2 text-3xl font-semibold">Infrastructure deployment control plane</h1>
          </div>
          <button className="inline-flex w-fit items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white shadow-sm">
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
              ["Projects tracked", String(projects.length), isLoading ? "Loading API data" : "Stored locally"],
              ["Estimated spend", `$${totalCost}/mo`, "Simulation only"],
            ].map(([label, value, detail]) => (
              <article key={label} className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-500">{label}</p>
                <p className="mt-3 text-3xl font-semibold">{value}</p>
                <p className="mt-2 text-sm text-slate-500">{detail}</p>
              </article>
            ))}
          </div>

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-lg font-semibold">Projects</h2>
                <p className="text-sm text-slate-500">{deploymentCount} simulated deployments</p>
              </div>
              <form className="grid gap-3 sm:grid-cols-[1fr_120px_auto]" onSubmit={handleCreateProject}>
                <input
                  className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
                  onChange={(event) => setName(event.target.value)}
                  placeholder="New project name"
                  value={name}
                />
                <select
                  className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
                  onChange={(event) => setEnvironment(event.target.value)}
                  value={environment}
                >
                  <option value="dev">dev</option>
                  <option value="stage">stage</option>
                  <option value="prod">prod</option>
                </select>
                <button
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-signal px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isCreating}
                  type="submit"
                >
                  <Plus size={16} />
                  Create
                </button>
              </form>
            </div>
            {error ? <p className="border-b border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-800">{error}</p> : null}
            <div className="divide-y divide-slate-100">
              {projects.map((project) => (
                <div key={project.id} className="grid gap-4 px-5 py-4 md:grid-cols-[1fr_auto_auto_auto] md:items-center">
                  <div>
                    <h3 className="font-semibold">{project.name}</h3>
                    <p className="text-sm text-slate-500">
                      {project.cloud_provider} / {project.environment}
                    </p>
                  </div>
                  <span className="text-sm font-medium capitalize text-signal">{project.status}</span>
                  <span className="text-sm text-slate-600">ready for upload</span>
                  <span className="text-sm font-semibold">${project.monthly_cost}/mo</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
              <FileCode2 className="text-ink" size={20} />
              <div>
                <h2 className="text-lg font-semibold">Upload Template</h2>
                <p className="text-sm text-slate-500">Store a Terraform, YAML, JSON, or Bicep template for a project</p>
              </div>
            </div>
            <form className="grid gap-4 px-5 py-5 lg:grid-cols-[180px_1fr_auto]" onSubmit={handleUploadTemplate}>
              <select
                className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
                onChange={(event) => setSelectedProjectId(event.target.value)}
                value={selectedProjectId}
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
              <input
                accept=".tf,.yaml,.yml,.json,.bicep"
                className="h-10 rounded-md border border-slate-300 px-3 py-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-panel file:px-3 file:py-1 file:text-sm file:font-semibold"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                type="file"
              />
              <button
                className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isUploading || !selectedFile}
                type="submit"
              >
                <CloudUpload size={16} />
                Save
              </button>
            </form>
            {uploadResult ? (
              <div className="border-t border-slate-100 px-5 py-4 text-sm text-slate-600">
                Saved <span className="font-semibold text-[#172033]">{uploadResult.template.file_name}</span> as version{" "}
                <span className="font-semibold text-[#172033]">{uploadResult.template.version}</span> with{" "}
                <span className="font-semibold text-[#172033]">{uploadResult.resources.length}</span> parsed resources.
              </div>
            ) : null}
          </section>

          {deploymentPlan ? (
            <section className="rounded-md border border-slate-200 bg-white shadow-sm">
              <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-3">
                  <ListChecks className="text-signal" size={20} />
                  <div>
                    <h2 className="text-lg font-semibold">Deployment Plan</h2>
                    <p className="text-sm text-slate-500">{deploymentPlan.template_name}</p>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-3 text-center text-sm">
                  <div>
                    <p className="font-semibold text-signal">{deploymentPlan.summary.create}</p>
                    <p className="text-slate-500">create</p>
                  </div>
                  <div>
                    <p className="font-semibold text-ink">{deploymentPlan.summary.update}</p>
                    <p className="text-slate-500">update</p>
                  </div>
                  <div>
                    <p className="font-semibold text-danger">{deploymentPlan.summary.delete}</p>
                    <p className="text-slate-500">delete</p>
                  </div>
                  <div>
                    <p className="font-semibold text-ink">${deploymentPlan.estimated_monthly_cost}</p>
                    <p className="text-slate-500">monthly</p>
                  </div>
                </div>
                <button
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-signal px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isDeploying || !uploadResult}
                  onClick={handleDeployTemplate}
                  type="button"
                >
                  <Play size={16} />
                  Deploy
                </button>
              </div>
              <div className="divide-y divide-slate-100">
                {deploymentPlan.changes.map((change) => (
                  <div
                    className="grid gap-3 px-5 py-4 text-sm md:grid-cols-[90px_1fr_auto] md:items-center"
                    key={`${change.action}-${change.resource.type}-${change.resource.name}`}
                  >
                    <span className="w-fit rounded-md bg-emerald-50 px-2 py-1 font-semibold uppercase text-emerald-700">
                      {change.action}
                    </span>
                    <div>
                      <p className="font-semibold text-[#172033]">{change.resource.name}</p>
                      <p className="text-slate-500">
                        {change.resource.type} / {change.resource.region}
                      </p>
                    </div>
                    <span className="font-semibold text-[#172033]">${change.resource.estimated_monthly_cost}/mo</span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {latestDeployment ? (
            <section className="rounded-md border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                <div className="flex items-center gap-3">
                  <Activity className="text-signal" size={20} />
                  <div>
                    <h2 className="text-lg font-semibold">Latest Deployment</h2>
                    <p className="text-sm text-slate-500">{latestDeployment.plan.template_name}</p>
                  </div>
                </div>
                <span className="rounded-md bg-emerald-50 px-2 py-1 text-sm font-semibold capitalize text-emerald-700">
                  {latestDeployment.status}
                </span>
              </div>
              <div className="grid gap-3 px-5 py-5 md:grid-cols-5">
                {latestDeployment.steps.map((step) => (
                  <div className="rounded-md border border-slate-200 bg-panel p-3" key={step.name}>
                    <p className="text-sm font-semibold">{step.name}</p>
                    <p className="mt-2 text-xs capitalize text-signal">{step.status}</p>
                  </div>
                ))}
              </div>
            </section>
          ) : null}
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
              <ListChecks className="text-signal" />
              <h2 className="text-lg font-semibold">History</h2>
            </div>
            <div className="mt-5 space-y-3">
              {deployments.slice(0, 4).map((deployment) => (
                <div key={deployment.id} className="rounded-md bg-panel px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="truncate text-sm font-medium">{deployment.plan.template_name}</span>
                    <span className="text-xs font-semibold capitalize text-signal">{deployment.status}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">${deployment.plan.estimated_monthly_cost}/mo</p>
                </div>
              ))}
              {deployments.length === 0 ? <p className="text-sm text-slate-500">No deployment runs yet.</p> : null}
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
