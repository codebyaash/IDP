"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Background, Controls, MarkerType, MiniMap, ReactFlow, type Edge, type Node } from "@xyflow/react";
import {
  Activity,
  CloudUpload,
  ExternalLink,
  FileCode2,
  GitBranch,
  Layers3,
  ListChecks,
  Network,
  Play,
  Plus,
  RotateCcw,
  Server,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  createProject,
  deployTemplate,
  fetchCostEstimate,
  fetchDeployments,
  fetchProjects,
  fetchResources,
  login,
  planTemplate,
  register,
  rollbackDeployment,
  type CostEstimate,
  type Deployment,
  type DeploymentPlan,
  type PersistedResource,
  type Project,
  type TemplateUploadResult,
  uploadTemplate,
} from "@/lib/api";

const fallbackProjects: Project[] = [
  {
    id: "demo-azure-core",
    user_id: "demo-user",
    organization_id: "deployforge.local",
    name: "Azure Core Network",
    cloud_provider: "azure",
    environment: "dev",
    status: "healthy",
    monthly_cost: 63,
    created_at: new Date().toISOString(),
  },
];

const pipeline = ["Queued", "Validating", "Planning", "Deploying", "Success"];
const TOKEN_STORAGE_KEY = "deployforge_token";
const DEMO_EMAIL = "ash@deployforge.local";
const DEMO_PASSWORD = "ashtest123";
const deploymentEnvironments = ["dev", "stage", "prod"];
const graphFilterAll = "all";

function resourceVisual(resourceType: string) {
  if (resourceType.includes("storage")) {
    return { accent: "#2a9d8f", background: "#f0fdfa", label: "Storage" };
  }
  if (resourceType.includes("virtual_machine") || resourceType === "vm") {
    return { accent: "#4f46e5", background: "#eef2ff", label: "Compute" };
  }
  if (resourceType.includes("network") || resourceType.includes("subnet") || resourceType.includes("public_ip")) {
    return { accent: "#0f766e", background: "#ecfeff", label: "Network" };
  }
  if (resourceType.includes("resource_group")) {
    return { accent: "#64748b", background: "#f8fafc", label: "Group" };
  }
  return { accent: "#a16207", background: "#fefce8", label: "Service" };
}

export function ProjectDashboard() {
  const [projects, setProjects] = useState<Project[]>(fallbackProjects);
  const [name, setName] = useState("");
  const [environment, setEnvironment] = useState("dev");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState(fallbackProjects[0].id);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [deploymentEnvironment, setDeploymentEnvironment] = useState("dev");
  const [uploadResult, setUploadResult] = useState<TemplateUploadResult | null>(null);
  const [deploymentPlan, setDeploymentPlan] = useState<DeploymentPlan | null>(null);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [latestDeployment, setLatestDeployment] = useState<Deployment | null>(null);
  const [resources, setResources] = useState<PersistedResource[]>([]);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [graphFilter, setGraphFilter] = useState(graphFilterAll);
  const [selectedGraphResourceName, setSelectedGraphResourceName] = useState<string | null>(null);
  const [isDeploying, setIsDeploying] = useState(false);
  const [rollbackDeploymentId, setRollbackDeploymentId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (storedToken) {
      setToken(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }

    setIsLoading(true);
    fetchProjects(token)
      .then((data) => {
        setProjects(data);
        setSelectedProjectId((current) => current || data[0]?.id || "");
        setError("");
      })
      .catch(() => {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
        setToken(null);
        setError("Session expired. Sign in again to continue.");
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  useEffect(() => {
    if (!selectedProjectId || !token) {
      return;
    }

    fetchDeployments(selectedProjectId, token, deploymentEnvironment)
      .then((data) => {
        setDeployments(data);
        setLatestDeployment(data[0] ?? null);
      })
      .catch(() => {
        setDeployments([]);
      });

    fetchResources(selectedProjectId, token, deploymentEnvironment)
      .then((data) => {
        setResources(data);
      })
      .catch(() => {
        setResources([]);
      });

    fetchCostEstimate(selectedProjectId, token, deploymentEnvironment)
      .then((data) => {
        setCostEstimate(data);
      })
      .catch(() => {
        setCostEstimate(null);
      });
  }, [deploymentEnvironment, selectedProjectId, token]);

  const totalCost = useMemo(() => projects.reduce((sum, project) => sum + project.monthly_cost, 0), [projects]);
  const deploymentCount = projects.length * 7;
  const resourceTypeCostData = costEstimate?.breakdown ?? [];
  const resourceTypes = useMemo(
    () => [graphFilterAll, ...Array.from(new Set(resources.map((resource) => resource.resource_type))).sort()],
    [resources],
  );
  const visibleGraphResources = useMemo(
    () =>
      graphFilter === graphFilterAll
        ? resources
        : resources.filter((resource) => resource.resource_type === graphFilter),
    [graphFilter, resources],
  );
  const selectedGraphResource =
    resources.find((resource) => resource.resource_name === selectedGraphResourceName) ?? visibleGraphResources[0] ?? null;
  const graphStats = useMemo(() => {
    const resourceNames = new Set(resources.map((resource) => resource.resource_name));
    const dependencyCount = resources.reduce((sum, resource) => sum + resource.dependencies.length, 0);
    const unresolvedDependencyCount = resources.reduce(
      (sum, resource) => sum + resource.dependencies.filter((dependency) => !resourceNames.has(dependency)).length,
      0,
    );
    const rootCount = resources.filter((resource) => resource.dependencies.length === 0).length;

    return { dependencyCount, rootCount, unresolvedDependencyCount };
  }, [resources]);
  const graphNodes = useMemo<Node[]>(
    () => {
      const resourcesByName = new Map(resources.map((resource) => [resource.resource_name, resource]));
      const depthCache = new Map<string, number>();
      const depthForResource = (resource: PersistedResource, visiting = new Set<string>()): number => {
        if (depthCache.has(resource.resource_name)) {
          return depthCache.get(resource.resource_name) ?? 0;
        }
        if (visiting.has(resource.resource_name)) {
          return 0;
        }
        const nextVisiting = new Set(visiting).add(resource.resource_name);
        const parentDepths = resource.dependencies
          .map((dependency) => resourcesByName.get(dependency))
          .filter((dependency): dependency is PersistedResource => Boolean(dependency))
          .map((dependency) => depthForResource(dependency, nextVisiting));
        const depth = parentDepths.length > 0 ? Math.max(...parentDepths) + 1 : 0;
        depthCache.set(resource.resource_name, depth);
        return depth;
      };
      const depthIndexes = new Map<number, number>();

      return visibleGraphResources.map((resource) => {
        const visual = resourceVisual(resource.resource_type);
        const isSelected = selectedGraphResource?.resource_name === resource.resource_name;
        const depth = depthForResource(resource);
        const depthIndex = depthIndexes.get(depth) ?? 0;
        depthIndexes.set(depth, depthIndex + 1);

        return {
          id: resource.resource_name,
          position: { x: depth * 250, y: depthIndex * 126 },
          data: {
            label: (
              <div className="text-left">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-semibold">{resource.resource_name}</p>
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: visual.accent }} />
                </div>
                <p className="mt-1 truncate text-xs text-slate-500">{resource.resource_type}</p>
                <div className="mt-2 flex items-center justify-between gap-2 text-xs">
                  <span className="font-semibold" style={{ color: visual.accent }}>
                    {visual.label}
                  </span>
                  <span className="text-slate-600">${resource.estimated_monthly_cost}/mo</span>
                </div>
              </div>
            ),
          },
          style: {
            width: 196,
            border: `1px solid ${isSelected ? visual.accent : "#cbd5e1"}`,
            borderRadius: 8,
            background: isSelected ? visual.background : "#ffffff",
            color: "#172033",
            padding: 12,
            boxShadow: isSelected ? `0 0 0 3px ${visual.accent}20` : "0 1px 2px rgb(15 23 42 / 0.06)",
          },
        };
      });
    },
    [resources, selectedGraphResource?.resource_name, visibleGraphResources],
  );
  const graphEdges = useMemo<Edge[]>(() => {
    const visibleNames = new Set(visibleGraphResources.map((resource) => resource.resource_name));

    return visibleGraphResources.flatMap((resource) =>
      resource.dependencies
        .filter((dependency) => visibleNames.has(dependency))
        .map((dependency) => ({
          id: `${dependency}-${resource.resource_name}`,
          source: dependency,
          target: resource.resource_name,
          animated: selectedGraphResourceName
            ? dependency === selectedGraphResourceName || resource.resource_name === selectedGraphResourceName
            : true,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#2a9d8f" },
          style: {
            stroke:
              dependency === selectedGraphResourceName || resource.resource_name === selectedGraphResourceName
                ? "#172033"
                : "#2a9d8f",
            strokeWidth:
              dependency === selectedGraphResourceName || resource.resource_name === selectedGraphResourceName ? 2.5 : 1.5,
          },
          type: "smoothstep",
        })),
    );
  }, [selectedGraphResourceName, visibleGraphResources]);
  const selectedGraphDependents = useMemo(
    () =>
      selectedGraphResource
        ? resources.filter((resource) => resource.dependencies.includes(selectedGraphResource.resource_name))
        : [],
    [resources, selectedGraphResource],
  );
  const selectedGraphMetadata = useMemo(() => {
    if (!selectedGraphResource) {
      return [];
    }
    return Object.entries(selectedGraphResource.resource_metadata).slice(0, 4);
  }, [selectedGraphResource]);

  useEffect(() => {
    if (resources.length === 0) {
      setSelectedGraphResourceName(null);
      setGraphFilter(graphFilterAll);
      return;
    }
    if (selectedGraphResourceName && resources.some((resource) => resource.resource_name === selectedGraphResourceName)) {
      return;
    }
    setSelectedGraphResourceName(resources[0].resource_name);
  }, [resources, selectedGraphResourceName]);

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim() || !token) {
      return;
    }

    setIsCreating(true);
    try {
      const project = await createProject({
        name: name.trim(),
        cloud_provider: "azure",
        environment,
      }, token);
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
    if (!selectedProjectId || !selectedFile || !token) {
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadTemplate(selectedProjectId, selectedFile, token, deploymentEnvironment);
      const plan = await planTemplate(result.template.id, token);
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
    if (!uploadResult || !token) {
      return;
    }

    setIsDeploying(true);
    try {
      const deployment = await deployTemplate(uploadResult.template.id, token);
      const [nextResources, nextCostEstimate] = await Promise.all([
        fetchResources(deployment.project_id, token, deployment.environment),
        fetchCostEstimate(deployment.project_id, token, deployment.environment),
      ]);
      setLatestDeployment(deployment);
      setDeployments((current) => [deployment, ...current.filter((item) => item.id !== deployment.id)]);
      setResources(nextResources);
      setCostEstimate(nextCostEstimate);
      setProjects((current) =>
        current.map((project) =>
          project.id === deployment.project_id
            ? { ...project, monthly_cost: nextCostEstimate.total_monthly_cost, status: "deployed" }
            : project,
        ),
      );
      setError("");
    } catch {
      setError("Could not run deployment simulation for this template.");
    } finally {
      setIsDeploying(false);
    }
  }

  async function handleRollback(deploymentId: string) {
    if (!token) {
      return;
    }

    setRollbackDeploymentId(deploymentId);
    try {
      const result = await rollbackDeployment(deploymentId, token, "Rollback from dashboard");
      const restoredDeployment = result.rollback_deployment;
      const [nextResources, nextCostEstimate, nextDeployments] = await Promise.all([
        fetchResources(restoredDeployment.project_id, token, restoredDeployment.environment),
        fetchCostEstimate(restoredDeployment.project_id, token, restoredDeployment.environment),
        fetchDeployments(restoredDeployment.project_id, token, restoredDeployment.environment),
      ]);
      setLatestDeployment(restoredDeployment);
      setDeployments(nextDeployments);
      setResources(nextResources);
      setCostEstimate(nextCostEstimate);
      setProjects((current) =>
        current.map((project) =>
          project.id === restoredDeployment.project_id
            ? { ...project, monthly_cost: nextCostEstimate.total_monthly_cost, status: "rolled_back" }
            : project,
        ),
      );
      setError("");
    } catch {
      setError("Could not roll back to that deployment.");
    } finally {
      setRollbackDeploymentId(null);
    }
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsAuthenticating(true);
    try {
      const response =
        authMode === "login" ? await login(email.trim(), password) : await register(email.trim(), password);
      window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setToken(response.access_token);
      setError("");
    } catch {
      setError(authMode === "login" ? "Could not sign in with those credentials." : "Could not create that account.");
    } finally {
      setIsAuthenticating(false);
    }
  }

  function handleLogout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setProjects(fallbackProjects);
    setDeployments([]);
    setLatestDeployment(null);
    setResources([]);
    setCostEstimate(null);
    setDeploymentPlan(null);
    setUploadResult(null);
    setDeploymentEnvironment("dev");
  }

  function handleDeploymentEnvironmentChange(nextEnvironment: string) {
    setDeploymentEnvironment(nextEnvironment);
    setDeploymentPlan(null);
    setUploadResult(null);
    setSelectedFile(null);
    setGraphFilter(graphFilterAll);
    setSelectedGraphResourceName(null);
  }

  if (!token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f6f8fb] px-6 text-[#172033]">
        <section className="w-full max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-signal">DeployForge</p>
          <h1 className="mt-2 text-2xl font-semibold">Sign in to your deployment workspace</h1>
          <form className="mt-6 space-y-4" onSubmit={handleAuth}>
            <input
              className="h-11 w-full rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email"
              type="email"
              value={email}
            />
            <input
              className="h-11 w-full rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              type="password"
              value={password}
            />
            {error ? <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{error}</p> : null}
            <button
              className="inline-flex h-11 w-full items-center justify-center rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isAuthenticating}
              type="submit"
            >
              {authMode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
          <div className="mt-4 flex items-center justify-between text-sm">
            <button
              className="font-semibold text-signal"
              onClick={() => setAuthMode((current) => (current === "login" ? "register" : "login"))}
              type="button"
            >
              {authMode === "login" ? "Create account" : "Use existing account"}
            </button>
            <span className="text-slate-500">Demo password is prefilled</span>
          </div>
        </section>
      </main>
    );
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
          <button
            className="inline-flex w-fit items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink"
            onClick={handleLogout}
            type="button"
          >
            Sign out
          </button>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[1.4fr_0.8fr]">
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["Success rate", "96%", "Last 30 days"],
              ["Projects tracked", String(projects.length), isLoading ? "Loading API data" : "Stored locally"],
              ["Estimated spend", `$${totalCost}/mo`, `${deploymentEnvironment} environment`],
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
            <form className="grid gap-4 px-5 py-5 lg:grid-cols-[180px_130px_1fr_auto]" onSubmit={handleUploadTemplate}>
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
              <select
                className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
                onChange={(event) => handleDeploymentEnvironmentChange(event.target.value)}
                value={deploymentEnvironment}
              >
                {deploymentEnvironments.map((item) => (
                  <option key={item} value={item}>
                    {item}
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
                <span className="font-semibold text-[#172033]">{uploadResult.resources.length}</span> parsed resources for{" "}
                <span className="font-semibold text-[#172033]">{uploadResult.template.environment}</span>.
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
                    <p className="text-sm text-slate-500">
                      {deploymentPlan.template_name} / {deploymentPlan.environment}
                    </p>
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
                <div className="grid gap-3 px-5 py-4 text-sm sm:grid-cols-4">
                  {[
                    ["creates", deploymentPlan.drift.creates],
                    ["updates", deploymentPlan.drift.updates],
                    ["deletes", deploymentPlan.drift.deletes],
                    ["unchanged", deploymentPlan.drift.unchanged],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-md border border-slate-200 bg-panel px-3 py-2">
                      <p className="text-lg font-semibold text-[#172033]">{value}</p>
                      <p className="text-xs uppercase text-slate-500">drift {label}</p>
                    </div>
                  ))}
                </div>
                {deploymentPlan.policy_violations.length > 0 ? (
                  <div className="bg-amber-50 px-5 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-amber-900">Policy checks</p>
                      <span className="rounded-md bg-amber-100 px-2 py-1 text-xs font-semibold uppercase text-amber-800">
                        {deploymentPlan.policy_violations.length} findings
                      </span>
                    </div>
                    <div className="mt-3 space-y-2">
                      {deploymentPlan.policy_violations.map((violation) => (
                        <div
                          className="grid gap-2 rounded-md border border-amber-200 bg-white px-3 py-2 text-sm md:grid-cols-[92px_1fr]"
                          key={`${violation.rule_id}-${violation.resource_name}`}
                        >
                          <span className="w-fit rounded-md bg-amber-100 px-2 py-1 text-xs font-semibold uppercase text-amber-800">
                            {violation.severity}
                          </span>
                          <div>
                            <p className="font-semibold text-amber-950">{violation.resource_name}</p>
                            <p className="text-amber-800">{violation.message}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
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
                    <p className="text-sm text-slate-500">
                      {latestDeployment.plan.template_name} / {latestDeployment.environment}
                    </p>
                  </div>
                </div>
                <span className="rounded-md bg-emerald-50 px-2 py-1 text-sm font-semibold capitalize text-emerald-700">
                  {latestDeployment.status}
                </span>
                <Link
                  className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
                  href={`/deployments/${latestDeployment.id}`}
                >
                  <ExternalLink size={16} />
                  Details
                </Link>
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

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center gap-3">
                <GitBranch className="text-ink" size={20} />
                <div>
                  <h2 className="text-lg font-semibold">Resource Graph</h2>
                  <p className="text-sm text-slate-500">
                    {deploymentEnvironment} / {resources.length} resources / {graphStats.dependencyCount} dependencies
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {resourceTypes.map((resourceType) => (
                  <button
                    className={`rounded-md border px-3 py-1.5 text-xs font-semibold ${
                      graphFilter === resourceType
                        ? "border-ink bg-ink text-white"
                        : "border-slate-300 bg-white text-ink"
                    }`}
                    key={resourceType}
                    onClick={() => setGraphFilter(resourceType)}
                    type="button"
                  >
                    {resourceType}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid gap-4 border-b border-slate-100 px-5 py-4 md:grid-cols-3">
              {[
                ["Roots", graphStats.rootCount, "no inbound dependencies"],
                ["Edges", graphStats.dependencyCount, "declared links"],
                ["Unresolved", graphStats.unresolvedDependencyCount, "missing references"],
              ].map(([label, value, detail]) => (
                <div className="rounded-md border border-slate-200 bg-panel px-4 py-3" key={label}>
                  <div className="flex items-center gap-2">
                    {label === "Roots" ? <Layers3 size={16} /> : label === "Edges" ? <Network size={16} /> : <Server size={16} />}
                    <p className="text-sm font-semibold">{label}</p>
                  </div>
                  <p className="mt-2 text-2xl font-semibold">{value}</p>
                  <p className="mt-1 text-xs text-slate-500">{detail}</p>
                </div>
              ))}
            </div>
            {graphNodes.length > 0 ? (
              <div className="grid gap-4 px-5 py-5 xl:grid-cols-[1fr_280px]">
                <div className="h-[480px] overflow-hidden rounded-md border border-slate-200 bg-panel">
                  <ReactFlow
                    edges={graphEdges}
                    fitView
                    minZoom={0.45}
                    nodes={graphNodes}
                    nodesConnectable={false}
                    nodesDraggable
                    onNodeClick={(_, node) => setSelectedGraphResourceName(String(node.id))}
                    proOptions={{ hideAttribution: true }}
                  >
                    <Background color="#cbd5e1" gap={18} />
                    <MiniMap
                      maskColor="rgb(241 245 249 / 0.72)"
                      nodeColor={(node) =>
                        selectedGraphResource?.resource_name === node.id
                          ? "#172033"
                          : resourceVisual(
                              resources.find((resource) => resource.resource_name === node.id)?.resource_type ?? "",
                            ).accent
                      }
                      pannable
                      zoomable
                    />
                    <Controls showInteractive={false} />
                  </ReactFlow>
                </div>
                <aside className="rounded-md border border-slate-200 bg-panel p-4">
                  {selectedGraphResource ? (
                    <div>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold">{selectedGraphResource.resource_name}</p>
                          <p className="mt-1 text-xs text-slate-500">{selectedGraphResource.resource_type}</p>
                        </div>
                        <span
                          className="rounded-md px-2 py-1 text-xs font-semibold"
                          style={{
                            backgroundColor: resourceVisual(selectedGraphResource.resource_type).background,
                            color: resourceVisual(selectedGraphResource.resource_type).accent,
                          }}
                        >
                          {resourceVisual(selectedGraphResource.resource_type).label}
                        </span>
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-md bg-white px-3 py-2">
                          <p className="text-xs text-slate-500">Region</p>
                          <p className="mt-1 font-semibold">{selectedGraphResource.region}</p>
                        </div>
                        <div className="rounded-md bg-white px-3 py-2">
                          <p className="text-xs text-slate-500">Monthly</p>
                          <p className="mt-1 font-semibold">${selectedGraphResource.estimated_monthly_cost}</p>
                        </div>
                      </div>
                      <div className="mt-4">
                        <p className="text-xs font-semibold uppercase text-slate-500">Depends on</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {selectedGraphResource.dependencies.length > 0 ? (
                            selectedGraphResource.dependencies.map((dependency) => (
                              <button
                                className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-ink"
                                key={dependency}
                                onClick={() => setSelectedGraphResourceName(dependency)}
                                type="button"
                              >
                                {dependency}
                              </button>
                            ))
                          ) : (
                            <span className="text-sm text-slate-500">None</span>
                          )}
                        </div>
                      </div>
                      <div className="mt-4">
                        <p className="text-xs font-semibold uppercase text-slate-500">Dependents</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {selectedGraphDependents.length > 0 ? (
                            selectedGraphDependents.map((resource) => (
                              <button
                                className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-ink"
                                key={resource.resource_name}
                                onClick={() => setSelectedGraphResourceName(resource.resource_name)}
                                type="button"
                              >
                                {resource.resource_name}
                              </button>
                            ))
                          ) : (
                            <span className="text-sm text-slate-500">None</span>
                          )}
                        </div>
                      </div>
                      {selectedGraphMetadata.length > 0 ? (
                        <div className="mt-4">
                          <p className="text-xs font-semibold uppercase text-slate-500">Metadata</p>
                          <div className="mt-2 space-y-2">
                            {selectedGraphMetadata.map(([key, value]) => (
                              <div className="rounded-md bg-white px-3 py-2 text-xs" key={key}>
                                <p className="font-semibold text-slate-600">{key}</p>
                                <p className="mt-1 truncate text-slate-500">
                                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">Select a resource node.</p>
                  )}
                </aside>
              </div>
            ) : (
              <p className="px-5 py-5 text-sm text-slate-500">Deploy a template to populate the dependency graph.</p>
            )}
            {resources.length > 0 ? (
              <div className="border-t border-slate-100 px-5 py-4">
                <div className="grid gap-2 text-sm">
                  {visibleGraphResources.map((resource) => (
                    <button
                      className="grid gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-left md:grid-cols-[1fr_150px_80px]"
                      key={resource.id}
                      onClick={() => setSelectedGraphResourceName(resource.resource_name)}
                      type="button"
                    >
                      <span className="truncate font-semibold">{resource.resource_name}</span>
                      <span className="truncate text-slate-500">{resource.resource_type}</span>
                      <span className="font-semibold text-ink">${resource.estimated_monthly_cost}/mo</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <Activity className="text-signal" />
              <h2 className="text-lg font-semibold">Pipeline</h2>
            </div>
            <div className="mt-5 space-y-3">
              {(latestDeployment?.steps.map((step) => step.name) ?? pipeline).map((stage, index) => (
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
                  <div className="mt-2 flex items-center justify-between gap-3">
                    <p className="text-xs text-slate-500">
                      ${deployment.plan.estimated_monthly_cost}/mo / {deployment.environment}
                    </p>
                    <div className="flex items-center gap-2">
                      <Link
                        className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold text-ink"
                        href={`/deployments/${deployment.id}`}
                      >
                        Details
                      </Link>
                      <button
                        className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={rollbackDeploymentId === deployment.id}
                        onClick={() => handleRollback(deployment.id)}
                        type="button"
                      >
                        Rollback
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {deployments.length === 0 ? <p className="text-sm text-slate-500">No deployment runs yet.</p> : null}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <Activity className="text-ink" />
              <h2 className="text-lg font-semibold">Cost Dashboard</h2>
            </div>
            {costEstimate && resourceTypeCostData.length > 0 ? (
              <>
                <div className="mt-4 flex items-end justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Current deployed monthly cost / {deploymentEnvironment}</p>
                    <p className="text-3xl font-semibold">${costEstimate.total_monthly_cost}</p>
                  </div>
                  <p className="text-sm text-slate-500">{costEstimate.resource_count} resources</p>
                </div>
                <div className="mt-5 h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={resourceTypeCostData}>
                      <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} />
                      <YAxis tickLine={false} axisLine={false} fontSize={12} />
                      <Tooltip />
                      <Bar dataKey="monthly_cost" fill="#2a9d8f" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </>
            ) : (
              <p className="mt-5 text-sm text-slate-500">No deployed resources yet, so there is no cost breakdown to chart.</p>
            )}
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
