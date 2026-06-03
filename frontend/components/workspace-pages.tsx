"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Background, Controls, MarkerType, MiniMap, ReactFlow, type Edge, type Node } from "@xyflow/react";
import {
  Activity,
  Boxes,
  CheckCircle2,
  ChevronRight,
  CloudUpload,
  DollarSign,
  ExternalLink,
  FileCode2,
  Filter,
  GitBranch,
  Home,
  IdCard,
  Layers3,
  ListChecks,
  LogOut,
  Network,
  Play,
  Plus,
  RotateCcw,
  Search,
  ShieldAlert,
  Upload,
  Users,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  createProject,
  deployTemplate,
  fetchCostEstimate,
  fetchDeployments,
  fetchProfile,
  fetchProjects,
  fetchResources,
  fetchTemplates,
  login,
  planTemplate,
  register,
  rollbackDeployment,
  type CostEstimate,
  type AuditLog,
  type Deployment,
  type DeploymentPlan,
  type PersistedResource,
  type Profile,
  type Project,
  type Template,
  type TemplateUploadResult,
  uploadTemplate,
} from "@/lib/api";

type WorkspaceMode =
  | "overview"
  | "projects"
  | "upload"
  | "deployments"
  | "resources"
  | "cost"
  | "profile"
  | "profile-history";

const TOKEN_STORAGE_KEY = "deployforge_token";
const SELECTED_PROJECT_KEY = "deployforge_selected_project";
const SELECTED_ENV_KEY = "deployforge_selected_environment";
const DEMO_EMAIL = "ash@deployforge.local";
const DEMO_PASSWORD = "ashtest123";
const environments = ["dev", "stage", "prod"];
const allStatuses = "all";
const allResourceTypes = "all";

const navigation = [
  { href: "/", label: "Overview", mode: "overview", icon: Home },
  { href: "/projects", label: "Projects", mode: "projects", icon: Boxes },
  { href: "/upload", label: "Upload & Plan", mode: "upload", icon: CloudUpload },
  { href: "/deployments", label: "Deployments", mode: "deployments", icon: Activity },
  { href: "/resources", label: "Resources", mode: "resources", icon: GitBranch },
  { href: "/cost", label: "Cost", mode: "cost", icon: DollarSign },
  { href: "/profile", label: "Profile", mode: "profile", icon: IdCard },
] satisfies Array<{ href: string; label: string; mode: WorkspaceMode; icon: typeof Home }>;

const quickLinks = [
  { title: "Upload & Plan", detail: "Upload IaC, inspect drift, and simulate deployment.", href: "/upload", icon: CloudUpload },
  { title: "Deployment History", detail: "Filter runs and open detailed pipeline logs.", href: "/deployments", icon: ListChecks },
  { title: "Resource Graph", detail: "Explore dependencies with React Flow.", href: "/resources", icon: GitBranch },
  { title: "Cost Dashboard", detail: "Review cost split by resource type.", href: "/cost", icon: DollarSign },
] satisfies Array<{ title: string; detail: string; href: string; icon: typeof Home }>;

function statusTone(status: string) {
  if (status === "success" || status === "deployed" || status === "healthy") {
    return "bg-emerald-50 text-emerald-700 border-emerald-200";
  }
  if (status === "failed") {
    return "bg-rose-50 text-rose-700 border-rose-200";
  }
  if (status === "rolled_back") {
    return "bg-indigo-50 text-indigo-700 border-indigo-200";
  }
  return "bg-slate-50 text-slate-700 border-slate-200";
}

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

function dateLabel(value: string | null) {
  if (!value) {
    return "Not recorded";
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function WorkspacePage({ mode }: { mode: WorkspaceMode }) {
  const pathname = usePathname();
  const [token, setToken] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedEnvironment, setSelectedEnvironment] = useState("dev");
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [resources, setResources] = useState<PersistedResource[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);

  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectEnvironment, setNewProjectEnvironment] = useState("dev");
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [uploadResult, setUploadResult] = useState<TemplateUploadResult | null>(null);
  const [deploymentPlan, setDeploymentPlan] = useState<DeploymentPlan | null>(null);
  const [rollbackDeploymentId, setRollbackDeploymentId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState(allStatuses);
  const [searchTerm, setSearchTerm] = useState("");
  const [resourceTypeFilter, setResourceTypeFilter] = useState(allResourceTypes);
  const [selectedResourceName, setSelectedResourceName] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    const storedEnvironment = window.localStorage.getItem(SELECTED_ENV_KEY);
    const storedProject = window.localStorage.getItem(SELECTED_PROJECT_KEY);

    if (storedEnvironment && environments.includes(storedEnvironment)) {
      setSelectedEnvironment(storedEnvironment);
      setNewProjectEnvironment(storedEnvironment);
    }
    if (storedProject) {
      setSelectedProjectId(storedProject);
    }
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
    Promise.all([fetchProjects(token), fetchProfile(token)])
      .then(([data, nextProfile]) => {
        setProjects(data);
        setProfile(nextProfile);
        setSelectedProjectId((current) => {
          const preferred = data.some((project) => project.id === current) ? current : data[0]?.id ?? "";
          if (preferred) {
            window.localStorage.setItem(SELECTED_PROJECT_KEY, preferred);
          }
          return preferred;
        });
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
    if (!token || !selectedProjectId) {
      setDeployments([]);
      setResources([]);
      setTemplates([]);
      setCostEstimate(null);
      return;
    }

    window.localStorage.setItem(SELECTED_PROJECT_KEY, selectedProjectId);
    window.localStorage.setItem(SELECTED_ENV_KEY, selectedEnvironment);
    Promise.all([
      fetchDeployments(selectedProjectId, token, selectedEnvironment),
      fetchResources(selectedProjectId, token, selectedEnvironment),
      fetchCostEstimate(selectedProjectId, token, selectedEnvironment),
      fetchTemplates(selectedProjectId, token, selectedEnvironment),
      fetchProfile(token),
    ])
      .then(([nextDeployments, nextResources, nextCostEstimate, nextTemplates, nextProfile]) => {
        setDeployments(nextDeployments);
        setResources(nextResources);
        setCostEstimate(nextCostEstimate);
        setTemplates(nextTemplates);
        setProfile(nextProfile);
        setError("");
      })
      .catch(() => {
        setDeployments([]);
        setResources([]);
        setCostEstimate(null);
        setTemplates([]);
      });
  }, [selectedEnvironment, selectedProjectId, token]);

  useEffect(() => {
    if (resources.length === 0) {
      setSelectedResourceName(null);
      return;
    }
    setSelectedResourceName((current) =>
      current && resources.some((resource) => resource.resource_name === current) ? current : resources[0].resource_name,
    );
  }, [resources]);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? projects[0] ?? null;
  const latestDeployment = deployments[0] ?? null;
  const totalPortfolioCost = projects.reduce((sum, project) => sum + project.monthly_cost, 0);
  const successRate =
    deployments.length > 0
      ? Math.round((deployments.filter((deployment) => deployment.status === "success").length / deployments.length) * 100)
      : 0;
  const policyFindingCount = deployments.reduce(
    (sum, deployment) => sum + deployment.plan.policy_violations.length,
    0,
  );

  const resourceTypes = useMemo(
    () => [allResourceTypes, ...Array.from(new Set(resources.map((resource) => resource.resource_type))).sort()],
    [resources],
  );
  const visibleResources = useMemo(
    () =>
      resourceTypeFilter === allResourceTypes
        ? resources
        : resources.filter((resource) => resource.resource_type === resourceTypeFilter),
    [resourceTypeFilter, resources],
  );
  const selectedResource =
    resources.find((resource) => resource.resource_name === selectedResourceName) ?? visibleResources[0] ?? null;
  const selectedDependents = selectedResource
    ? resources.filter((resource) => resource.dependencies.includes(selectedResource.resource_name))
    : [];

  const graphStats = useMemo(() => {
    const resourceNames = new Set(resources.map((resource) => resource.resource_name));
    return {
      roots: resources.filter((resource) => resource.dependencies.length === 0).length,
      dependencies: resources.reduce((sum, resource) => sum + resource.dependencies.length, 0),
      unresolved: resources.reduce(
        (sum, resource) => sum + resource.dependencies.filter((dependency) => !resourceNames.has(dependency)).length,
        0,
      ),
    };
  }, [resources]);

  const graphNodes = useMemo<Node[]>(() => {
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

    return visibleResources.map((resource) => {
      const visual = resourceVisual(resource.resource_type);
      const isSelected = selectedResource?.resource_name === resource.resource_name;
      const depth = depthForResource(resource);
      const depthIndex = depthIndexes.get(depth) ?? 0;
      depthIndexes.set(depth, depthIndex + 1);

      return {
        id: resource.resource_name,
        position: { x: depth * 250, y: depthIndex * 128 },
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
          width: 198,
          border: `1px solid ${isSelected ? visual.accent : "#cbd5e1"}`,
          borderRadius: 8,
          background: isSelected ? visual.background : "#ffffff",
          color: "#172033",
          padding: 12,
          boxShadow: isSelected ? `0 0 0 3px ${visual.accent}20` : "0 1px 2px rgb(15 23 42 / 0.06)",
        },
      };
    });
  }, [resources, selectedResource?.resource_name, visibleResources]);

  const graphEdges = useMemo<Edge[]>(() => {
    const visibleNames = new Set(visibleResources.map((resource) => resource.resource_name));
    return visibleResources.flatMap((resource) =>
      resource.dependencies
        .filter((dependency) => visibleNames.has(dependency))
        .map((dependency) => ({
          id: `${dependency}-${resource.resource_name}`,
          source: dependency,
          target: resource.resource_name,
          animated: selectedResourceName
            ? dependency === selectedResourceName || resource.resource_name === selectedResourceName
            : true,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#2a9d8f" },
          style: {
            stroke:
              dependency === selectedResourceName || resource.resource_name === selectedResourceName
                ? "#172033"
                : "#2a9d8f",
            strokeWidth:
              dependency === selectedResourceName || resource.resource_name === selectedResourceName ? 2.5 : 1.5,
          },
          type: "smoothstep",
        })),
    );
  }, [selectedResourceName, visibleResources]);

  const filteredDeployments = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    return deployments.filter((deployment) => {
      const statusMatches = statusFilter === allStatuses || deployment.status === statusFilter;
      const searchMatches =
        normalizedSearch.length === 0 ||
        deployment.plan.template_name.toLowerCase().includes(normalizedSearch) ||
        deployment.id.toLowerCase().includes(normalizedSearch);
      return statusMatches && searchMatches;
    });
  }, [deployments, searchTerm, statusFilter]);

  async function refreshWorkspace(projectId = selectedProjectId, environment = selectedEnvironment) {
    if (!token || !projectId) {
      return;
    }
    const [nextDeployments, nextResources, nextCostEstimate, nextTemplates, nextProjects, nextProfile] = await Promise.all([
      fetchDeployments(projectId, token, environment),
      fetchResources(projectId, token, environment),
      fetchCostEstimate(projectId, token, environment),
      fetchTemplates(projectId, token, environment),
      fetchProjects(token),
      fetchProfile(token),
    ]);
    setDeployments(nextDeployments);
    setResources(nextResources);
    setCostEstimate(nextCostEstimate);
    setTemplates(nextTemplates);
    setProjects(nextProjects);
    setProfile(nextProfile);
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsAuthenticating(true);
    try {
      const response = authMode === "login" ? await login(email.trim(), password) : await register(email.trim(), password);
      window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setToken(response.access_token);
      setProfile({
        user: response.user,
        activity: [],
        organization_activity: [],
        summary: {},
      });
      setError("");
    } catch {
      setError(authMode === "login" ? "Could not sign in with those credentials." : "Could not create that account.");
    } finally {
      setIsAuthenticating(false);
    }
  }

  function handleLogout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    window.localStorage.removeItem(SELECTED_PROJECT_KEY);
    setToken(null);
    setProjects([]);
    setDeployments([]);
    setResources([]);
    setTemplates([]);
    setCostEstimate(null);
    setProfile(null);
    setDeploymentPlan(null);
    setUploadResult(null);
  }

  function handleProjectChange(projectId: string) {
    setSelectedProjectId(projectId);
    window.localStorage.setItem(SELECTED_PROJECT_KEY, projectId);
    setDeploymentPlan(null);
    setUploadResult(null);
    setSelectedFile(null);
  }

  function handleEnvironmentChange(environment: string) {
    setSelectedEnvironment(environment);
    setNewProjectEnvironment(environment);
    window.localStorage.setItem(SELECTED_ENV_KEY, environment);
    setDeploymentPlan(null);
    setUploadResult(null);
    setSelectedFile(null);
    setResourceTypeFilter(allResourceTypes);
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newProjectName.trim() || !token) {
      return;
    }
    setIsCreatingProject(true);
    try {
      const project = await createProject(
        { name: newProjectName.trim(), cloud_provider: "azure", environment: newProjectEnvironment },
        token,
      );
      setProjects((current) => [project, ...current]);
      handleProjectChange(project.id);
      handleEnvironmentChange(project.environment);
      setNewProjectName("");
      setError("");
    } catch {
      setError("Could not create project. Check that the API server is running.");
    } finally {
      setIsCreatingProject(false);
    }
  }

  async function handleUploadTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProjectId || !selectedFile || !token) {
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadTemplate(selectedProjectId, selectedFile, token, selectedEnvironment);
      const plan = await planTemplate(result.template.id, token);
      await refreshWorkspace(selectedProjectId, selectedEnvironment);
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
      await refreshWorkspace(deployment.project_id, deployment.environment);
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
      const result = await rollbackDeployment(deploymentId, token, "Rollback from deployments page");
      await refreshWorkspace(result.rollback_deployment.project_id, result.rollback_deployment.environment);
      setError("");
    } catch {
      setError("Could not roll back to that deployment.");
    } finally {
      setRollbackDeploymentId(null);
    }
  }

  if (!token) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6 py-10 text-[#172033]">
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
    <main className="min-h-screen text-[#172033]">
      <div className="mx-auto grid min-h-screen max-w-[1600px] lg:grid-cols-[250px_1fr]">
        <aside className="border-b border-slate-200 bg-white/90 px-5 py-5 backdrop-blur lg:border-b-0 lg:border-r">
          <div className="flex items-center justify-between gap-3 lg:block">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-signal">DeployForge</p>
              <p className="mt-1 text-xs text-slate-500">Infrastructure control plane</p>
            </div>
            <button
              className="inline-flex h-9 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-semibold text-ink lg:mt-6"
              onClick={handleLogout}
              type="button"
            >
              <LogOut size={15} />
              Sign out
            </button>
          </div>
          <nav className="mt-5 grid gap-1 sm:grid-cols-3 lg:grid-cols-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href === "/profile" && pathname.startsWith("/profile"));
              return (
                <Link
                  className={`flex h-10 items-center gap-3 rounded-md px-3 text-sm font-semibold ${
                    isActive ? "bg-ink text-white" : "text-slate-600 hover:bg-panel hover:text-ink"
                  }`}
                  href={item.href}
                  key={item.href}
                >
                  <Icon size={17} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <section className="px-5 py-6 md:px-8">
          <header className="flex flex-col gap-4 border-b border-slate-200 pb-6 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-signal">
                {navigation.find((item) => item.mode === mode)?.label}
              </p>
              <h1 className="mt-2 text-3xl font-semibold">{pageTitle(mode)}</h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-500">{pageDescription(mode)}</p>
            </div>
            <div className="grid gap-3 rounded-md border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-[220px_130px]">
              <label className="text-xs font-semibold uppercase text-slate-500">
                Project
                <select
                  className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm font-normal normal-case text-[#172033] outline-none focus:border-signal"
                  onChange={(event) => handleProjectChange(event.target.value)}
                  value={selectedProjectId}
                >
                  {projects.length === 0 ? <option value="">No projects</option> : null}
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs font-semibold uppercase text-slate-500">
                Environment
                <select
                  className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm font-normal normal-case text-[#172033] outline-none focus:border-signal"
                  onChange={(event) => handleEnvironmentChange(event.target.value)}
                  value={selectedEnvironment}
                >
                  {environments.map((environment) => (
                    <option key={environment} value={environment}>
                      {environment}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </header>

          {error ? <p className="mt-5 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</p> : null}
          {isLoading ? <p className="mt-8 rounded-md border border-slate-200 bg-white p-5 text-sm text-slate-500">Loading workspace...</p> : null}

          <div className="mt-6">{renderMode()}</div>
        </section>
      </div>
    </main>
  );

  function renderMode() {
    if (mode === "overview") {
      return (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <StatCard label="Projects" value={projects.length} detail="owned workspaces" icon={<Boxes size={18} />} />
            <StatCard label="Deployments" value={deployments.length} detail={`${selectedEnvironment} runs`} icon={<Activity size={18} />} />
            <StatCard label="Success rate" value={`${successRate}%`} detail="selected environment" icon={<CheckCircle2 size={18} />} />
            <StatCard label="Resources" value={resources.length} detail="latest snapshot" icon={<Network size={18} />} />
            <StatCard label="Monthly cost" value={`$${costEstimate?.total_monthly_cost ?? totalPortfolioCost}`} detail="estimated" icon={<DollarSign size={18} />} />
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
            <section className="rounded-md border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                <div>
                  <h2 className="text-lg font-semibold">Recent Deployments</h2>
                  <p className="text-sm text-slate-500">Latest activity for {selectedProject?.name ?? "your workspace"}</p>
                </div>
                <Link className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink" href="/deployments">
                  View history
                  <ChevronRight size={16} />
                </Link>
              </div>
              <div className="divide-y divide-slate-100">
                {deployments.slice(0, 5).map((deployment) => (
                  <DeploymentRow deployment={deployment} key={deployment.id} onRollback={handleRollback} rollbackDeploymentId={rollbackDeploymentId} />
                ))}
                {deployments.length === 0 ? <EmptyState text="Upload and deploy a sample template to populate deployment activity." /> : null}
              </div>
            </section>

            <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Environment Snapshot</h2>
              <div className="mt-5 grid gap-3">
                <SnapshotLine label="Active project" value={selectedProject?.name ?? "None"} />
                <SnapshotLine label="Environment" value={selectedEnvironment} />
                <SnapshotLine label="Saved templates" value={templates.length} />
                <SnapshotLine label="Policy findings" value={policyFindingCount} />
                <SnapshotLine label="Last deployment" value={latestDeployment ? dateLabel(latestDeployment.created_at) : "No runs"} />
              </div>
            </section>
          </div>

          <section className="grid gap-4 md:grid-cols-4">
            {quickLinks.map(({ detail, href, icon: Icon, title }) => (
              <Link className="rounded-md border border-slate-200 bg-white p-5 shadow-sm transition hover:border-signal" href={href} key={title}>
                <Icon className="text-signal" size={21} />
                <p className="mt-4 font-semibold">{title}</p>
                <p className="mt-2 text-sm text-slate-500">{detail}</p>
              </Link>
            ))}
          </section>
        </div>
      );
    }

    if (mode === "projects") {
      return (
        <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Create Project</h2>
            <form className="mt-5 space-y-4" onSubmit={handleCreateProject}>
              <input
                className="h-11 w-full rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
                onChange={(event) => setNewProjectName(event.target.value)}
                placeholder="Project name"
                value={newProjectName}
              />
              <select
                className="h-11 w-full rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal"
                onChange={(event) => setNewProjectEnvironment(event.target.value)}
                value={newProjectEnvironment}
              >
                {environments.map((environment) => (
                  <option key={environment} value={environment}>
                    {environment}
                  </option>
                ))}
              </select>
              <button className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-signal px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={isCreatingProject} type="submit">
                <Plus size={16} />
                Create project
              </button>
            </form>
          </section>

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-4">
              <h2 className="text-lg font-semibold">Project Inventory</h2>
              <p className="text-sm text-slate-500">Select a project to drive every workflow page.</p>
            </div>
            <div className="divide-y divide-slate-100">
              {projects.map((project) => (
                <button
                  className={`grid w-full gap-4 px-5 py-4 text-left md:grid-cols-[1fr_110px_120px_100px] md:items-center ${
                    project.id === selectedProjectId ? "bg-emerald-50/60" : "bg-white hover:bg-panel"
                  }`}
                  key={project.id}
                  onClick={() => {
                    handleProjectChange(project.id);
                    handleEnvironmentChange(project.environment);
                  }}
                  type="button"
                >
                  <div>
                    <p className="font-semibold">{project.name}</p>
                    <p className="mt-1 text-sm text-slate-500">{project.cloud_provider}</p>
                  </div>
                  <span className="text-sm font-semibold">{project.environment}</span>
                  <span className={`w-fit rounded-md border px-2 py-1 text-xs font-semibold capitalize ${statusTone(project.status)}`}>{project.status}</span>
                  <span className="font-semibold">${project.monthly_cost}/mo</span>
                </button>
              ))}
              {projects.length === 0 ? <EmptyState text="Create a project before uploading IaC templates." /> : null}
            </div>
          </section>
        </div>
      );
    }

    if (mode === "upload") {
      return (
        <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
          <div className="space-y-6">
            <section className="rounded-md border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
                <Upload className="text-signal" size={20} />
                <div>
                  <h2 className="text-lg font-semibold">Upload Template</h2>
                  <p className="text-sm text-slate-500">Terraform, YAML, JSON, and Bicep files are supported.</p>
                </div>
              </div>
              <form className="grid gap-4 px-5 py-5 lg:grid-cols-[1fr_auto]" onSubmit={handleUploadTemplate}>
                <input
                  accept=".tf,.yaml,.yml,.json,.bicep"
                  className="h-11 rounded-md border border-slate-300 px-3 py-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-panel file:px-3 file:py-1 file:text-sm file:font-semibold"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  type="file"
                />
                <button className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-ink px-5 text-sm font-semibold text-white disabled:opacity-60" disabled={isUploading || !selectedFile || !selectedProjectId} type="submit">
                  <CloudUpload size={16} />
                  Upload and plan
                </button>
              </form>
              {uploadResult ? (
                <p className="border-t border-slate-100 px-5 py-4 text-sm text-slate-600">
                  Saved <span className="font-semibold text-[#172033]">{uploadResult.template.file_name}</span> as version{" "}
                  <span className="font-semibold text-[#172033]">{uploadResult.template.version}</span> with{" "}
                  <span className="font-semibold text-[#172033]">{uploadResult.resources.length}</span> parsed resources.
                </p>
              ) : null}
            </section>

            {deploymentPlan ? (
              <section className="rounded-md border border-slate-200 bg-white shadow-sm">
                <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">Deployment Plan</h2>
                    <p className="text-sm text-slate-500">{deploymentPlan.template_name} / {deploymentPlan.environment}</p>
                  </div>
                  <button className="inline-flex h-10 w-fit items-center justify-center gap-2 rounded-md bg-signal px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={isDeploying || !uploadResult} onClick={handleDeployTemplate} type="button">
                    <Play size={16} />
                    Deploy simulation
                  </button>
                </div>
                <div className="grid gap-3 border-b border-slate-100 px-5 py-4 md:grid-cols-5">
                  <StatTile label="Create" value={deploymentPlan.summary.create ?? 0} />
                  <StatTile label="Update" value={deploymentPlan.summary.update ?? 0} />
                  <StatTile label="Delete" value={deploymentPlan.summary.delete ?? 0} />
                  <StatTile label="Unchanged" value={deploymentPlan.drift.unchanged} />
                  <StatTile label="Monthly" value={`$${deploymentPlan.estimated_monthly_cost}`} />
                </div>
                {deploymentPlan.policy_violations.length > 0 ? (
                  <div className="border-b border-amber-200 bg-amber-50 px-5 py-4">
                    <p className="text-sm font-semibold text-amber-950">Policy checks</p>
                    <div className="mt-3 grid gap-2">
                      {deploymentPlan.policy_violations.map((violation) => (
                        <div className="rounded-md border border-amber-200 bg-white px-3 py-2 text-sm" key={`${violation.rule_id}-${violation.resource_name}`}>
                          <p className="font-semibold text-amber-950">{violation.resource_name}</p>
                          <p className="mt-1 text-amber-800">{violation.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
                <div className="divide-y divide-slate-100">
                  {deploymentPlan.changes.map((change) => (
                    <div className="grid gap-3 px-5 py-4 text-sm md:grid-cols-[90px_1fr_auto]" key={`${change.action}-${change.resource.name}`}>
                      <span className="w-fit rounded-md bg-emerald-50 px-2 py-1 font-semibold uppercase text-emerald-700">{change.action}</span>
                      <div>
                        <p className="font-semibold">{change.resource.name}</p>
                        <p className="text-slate-500">{change.resource.type} / {change.reason}</p>
                      </div>
                      <span className="font-semibold">${change.resource.estimated_monthly_cost}/mo</span>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}
          </div>

          <section className="h-fit rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
              <FileCode2 className="text-ink" size={20} />
              <h2 className="text-lg font-semibold">Template History</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {templates.map((template) => (
                <div className="px-5 py-4 text-sm" key={template.id}>
                  <p className="font-semibold">{template.file_name}</p>
                  <p className="mt-1 text-slate-500">v{template.version} / {template.file_type} / {dateLabel(template.created_at)}</p>
                </div>
              ))}
              {templates.length === 0 ? <EmptyState text="No templates stored for this project and environment." /> : null}
            </div>
          </section>
        </div>
      );
    }

    if (mode === "deployments") {
      return (
        <section className="rounded-md border border-slate-200 bg-white shadow-sm">
          <div className="grid gap-3 border-b border-slate-200 px-5 py-4 lg:grid-cols-[1fr_170px_160px]">
            <label className="relative">
              <Search className="absolute left-3 top-3 text-slate-400" size={16} />
              <input className="h-10 w-full rounded-md border border-slate-300 pl-9 pr-3 text-sm outline-none focus:border-signal" onChange={(event) => setSearchTerm(event.target.value)} placeholder="Search template or deployment id" value={searchTerm} />
            </label>
            <select className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal" onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}>
              {[allStatuses, ...Array.from(new Set(deployments.map((deployment) => deployment.status))).sort()].map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
            <div className="inline-flex h-10 items-center gap-2 rounded-md bg-panel px-3 text-sm font-semibold text-slate-600">
              <Filter size={16} />
              {filteredDeployments.length} results
            </div>
          </div>
          <div className="divide-y divide-slate-100">
            {filteredDeployments.map((deployment) => (
              <DeploymentRow deployment={deployment} key={deployment.id} onRollback={handleRollback} rollbackDeploymentId={rollbackDeploymentId} />
            ))}
            {filteredDeployments.length === 0 ? <EmptyState text="No deployments match the selected project, environment, and filters." /> : null}
          </div>
        </section>
      );
    }

    if (mode === "resources") {
      return (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard label="Roots" value={graphStats.roots} detail="no declared dependency" icon={<Layers3 size={18} />} />
            <StatCard label="Edges" value={graphStats.dependencies} detail="dependency links" icon={<Network size={18} />} />
            <StatCard label="Unresolved" value={graphStats.unresolved} detail="missing references" icon={<ShieldAlert size={18} />} />
          </div>
          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-lg font-semibold">Resource Graph</h2>
                <p className="text-sm text-slate-500">{resources.length} resources in {selectedEnvironment}</p>
              </div>
              <select className="h-10 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-signal" onChange={(event) => setResourceTypeFilter(event.target.value)} value={resourceTypeFilter}>
                {resourceTypes.map((resourceType) => (
                  <option key={resourceType} value={resourceType}>
                    {resourceType}
                  </option>
                ))}
              </select>
            </div>
            {graphNodes.length > 0 ? (
              <div className="grid gap-4 px-5 py-5 xl:grid-cols-[1fr_320px]">
                <div className="h-[580px] overflow-hidden rounded-md border border-slate-200 bg-panel">
                  <ReactFlow edges={graphEdges} fitView minZoom={0.45} nodes={graphNodes} nodesConnectable={false} nodesDraggable onNodeClick={(_, node) => setSelectedResourceName(String(node.id))} proOptions={{ hideAttribution: true }}>
                    <Background color="#cbd5e1" gap={18} />
                    <MiniMap maskColor="rgb(241 245 249 / 0.72)" pannable zoomable />
                    <Controls showInteractive={false} />
                  </ReactFlow>
                </div>
                <ResourceInspector resource={selectedResource} dependents={selectedDependents} onSelect={setSelectedResourceName} />
              </div>
            ) : (
              <EmptyState text="Deploy a template to populate the resource graph." />
            )}
            {visibleResources.length > 0 ? (
              <div className="border-t border-slate-100 px-5 py-4">
                <div className="grid gap-2 text-sm">
                  {visibleResources.map((resource) => (
                    <button className="grid gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-left md:grid-cols-[1fr_180px_90px]" key={resource.id} onClick={() => setSelectedResourceName(resource.resource_name)} type="button">
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
      );
    }

    if (mode === "profile") {
      return (
        <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
          <div className="space-y-6">
            <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="rounded-md bg-panel p-2 text-ink">
                  <IdCard size={20} />
                </span>
                <div>
                  <h2 className="text-lg font-semibold">User Info</h2>
                  <p className="text-sm text-slate-500">Signed-in profile and organization context.</p>
                </div>
              </div>
              <div className="mt-5 grid gap-3">
                <SnapshotLine label="Email" value={profile?.user.email ?? "Loading"} />
                <SnapshotLine label="Organization" value={profile?.user.organization_name ?? "Loading"} />
                <SnapshotLine label="Org ID" value={profile?.user.organization_id ?? "Loading"} />
                <SnapshotLine label="Joined" value={profile?.user.created_at ? dateLabel(profile.user.created_at) : "Loading"} />
              </div>
            </section>

            <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <Users className="text-signal" size={20} />
                <h2 className="text-lg font-semibold">Personal Summary</h2>
              </div>
              <div className="mt-5 grid gap-3">
                {Object.entries(profile?.summary ?? {}).length > 0 ? (
                  Object.entries(profile?.summary ?? {}).map(([action, count]) => (
                    <SnapshotLine key={action} label={action.replaceAll("_", " ")} value={count} />
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No tracked activity yet.</p>
                )}
              </div>
            </section>
          </div>

          <div className="space-y-6">
            <ActivityFeed
              description="Actions performed by the signed-in user."
              items={(profile?.activity ?? []).slice(0, 5)}
              linkHref="/profile/history#your-history"
              linkLabel="View all"
              title="Your History"
            />
            <ActivityFeed
              description="Recent actions from users in the same organization."
              items={(profile?.organization_activity ?? []).slice(0, 5)}
              linkHref="/profile/history#organization-history"
              linkLabel="View all"
              title="Organization History"
            />
          </div>
        </div>
      );
    }

    if (mode === "profile-history") {
      return (
        <div className="space-y-6">
          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-semibold">Activity Archive</h2>
                <p className="text-sm text-slate-500">
                  {profile?.user.email ?? "Current user"} / {profile?.user.organization_name ?? "organization"}
                </p>
              </div>
              <Link
                className="inline-flex w-fit items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
                href="/profile"
              >
                Profile overview
                <ChevronRight size={16} />
              </Link>
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-2">
            <div id="your-history">
              <ActivityFeed
                description="Complete action trail for the signed-in user."
                items={profile?.activity ?? []}
                title="Your Full History"
              />
            </div>
            <div id="organization-history">
              <ActivityFeed
                description="Complete recent action trail for users in the same organization."
                items={profile?.organization_activity ?? []}
                title="Organization Full History"
              />
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-end justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Monthly Cost Breakdown</h2>
              <p className="mt-1 text-sm text-slate-500">{selectedProject?.name ?? "Project"} / {selectedEnvironment}</p>
            </div>
            <p className="text-3xl font-semibold">${costEstimate?.total_monthly_cost ?? 0}</p>
          </div>
          <div className="mt-6 h-[360px]">
            {costEstimate && costEstimate.breakdown.length > 0 ? (
              <ResponsiveContainer height="100%" width="100%">
                <BarChart data={costEstimate.breakdown}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} />
                  <YAxis tickLine={false} axisLine={false} fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="monthly_cost" fill="#2a9d8f" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState text="Deploy resources to generate a cost estimate." />
            )}
          </div>
        </section>
        <section className="h-fit rounded-md border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-semibold">Resource Cost Table</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {(costEstimate?.breakdown ?? []).map((item) => (
              <div className="grid grid-cols-[1fr_auto] gap-4 px-5 py-4 text-sm" key={item.label}>
                <div>
                  <p className="font-semibold">{item.label}</p>
                  <p className="mt-1 text-slate-500">{item.resource_count} resources</p>
                </div>
                <span className="font-semibold">${item.monthly_cost}/mo</span>
              </div>
            ))}
            {!costEstimate || costEstimate.breakdown.length === 0 ? <EmptyState text="No cost data for this filter." /> : null}
          </div>
        </section>
      </div>
    );
  }
}

function pageTitle(mode: WorkspaceMode) {
  const titles: Record<WorkspaceMode, string> = {
    overview: "Workspace overview",
    projects: "Projects and ownership",
    upload: "Template upload, drift, and policy checks",
    deployments: "Deployment history",
    resources: "Resource graph",
    cost: "Cost dashboard",
    profile: "Profile and activity history",
    "profile-history": "Activity history",
  };
  return titles[mode];
}

function pageDescription(mode: WorkspaceMode) {
  const descriptions: Record<WorkspaceMode, string> = {
    overview: "High-level health, recent activity, and cost posture for the selected project and environment.",
    projects: "Create projects, switch ownership context, and choose the environment used by the workflow pages.",
    upload: "Upload IaC templates, generate a plan, review drift and policy findings, then run the simulated deployment.",
    deployments: "Search and filter deployment runs, inspect details, and trigger rollback workflows.",
    resources: "Explore the latest persisted deployment resources and dependency relationships.",
    cost: "Review monthly cost estimates by resource type for the selected project and environment.",
    profile: "Review your account, organization, personal activity, and shared organization history.",
    "profile-history": "Open the full personal and organization activity history from your profile overview.",
  };
  return descriptions[mode];
}

function StatCard({ label, value, detail, icon }: { label: string; value: string | number; detail: string; icon: React.ReactNode }) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-500">{label}</p>
        <span className="rounded-md bg-panel p-2 text-ink">{icon}</span>
      </div>
      <p className="mt-4 text-3xl font-semibold">{value}</p>
      <p className="mt-2 text-sm text-slate-500">{detail}</p>
    </article>
  );
}

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-panel px-4 py-3">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="mt-1 text-xs font-semibold uppercase text-slate-500">{label}</p>
    </div>
  );
}

function SnapshotLine({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-md bg-panel px-3 py-2 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="truncate font-semibold">{value}</span>
    </div>
  );
}

function DeploymentRow({
  deployment,
  onRollback,
  rollbackDeploymentId,
}: {
  deployment: Deployment;
  onRollback: (deploymentId: string) => void;
  rollbackDeploymentId: string | null;
}) {
  return (
    <div className="grid gap-4 px-5 py-4 md:grid-cols-[1fr_120px_120px_190px] md:items-center">
      <div>
        <p className="font-semibold">{deployment.plan.template_name}</p>
        <p className="mt-1 text-xs text-slate-500">{deployment.id}</p>
      </div>
      <span className={`w-fit rounded-md border px-2 py-1 text-xs font-semibold capitalize ${statusTone(deployment.status)}`}>
        {deployment.status}
      </span>
      <span className="text-sm font-semibold">${deployment.plan.estimated_monthly_cost}/mo</span>
      <div className="flex flex-wrap items-center gap-2">
        <Link className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold text-ink" href={`/deployments/${deployment.id}`}>
          <ExternalLink size={14} />
          Details
        </Link>
        <button
          className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold text-ink disabled:opacity-60"
          disabled={rollbackDeploymentId === deployment.id}
          onClick={() => onRollback(deployment.id)}
          type="button"
        >
          <RotateCcw size={14} />
          Rollback
        </button>
      </div>
    </div>
  );
}

function ActivityFeed({
  description,
  items,
  linkHref,
  linkLabel,
  title,
}: {
  description: string;
  items: AuditLog[];
  linkHref?: string;
  linkLabel?: string;
  title: string;
}) {
  return (
    <section className="rounded-md border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-slate-500">{description}</p>
        </div>
        {linkHref && linkLabel ? (
          <Link
            className="inline-flex w-fit items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
            href={linkHref}
          >
            {linkLabel}
            <ChevronRight size={16} />
          </Link>
        ) : null}
      </div>
      <div className="divide-y divide-slate-100">
        {items.map((item) => (
          <div className="grid gap-3 px-5 py-4 text-sm md:grid-cols-[160px_1fr_auto]" key={item.id}>
            <div>
              <p className="font-semibold capitalize">{item.action.replaceAll("_", " ")}</p>
              <p className="mt-1 text-xs text-slate-500">{dateLabel(item.created_at)}</p>
            </div>
            <div>
              <p className="font-medium">{item.message}</p>
              <p className="mt-1 text-xs text-slate-500">
                {item.entity_type}
                {item.environment ? ` / ${item.environment}` : ""}
              </p>
            </div>
            {item.project_id ? <span className="rounded-md bg-panel px-2 py-1 text-xs font-semibold text-slate-600">project</span> : null}
          </div>
        ))}
        {items.length === 0 ? <EmptyState text="No activity has been tracked yet." /> : null}
      </div>
    </section>
  );
}

function ResourceInspector({
  resource,
  dependents,
  onSelect,
}: {
  resource: PersistedResource | null;
  dependents: PersistedResource[];
  onSelect: (resourceName: string) => void;
}) {
  if (!resource) {
    return <aside className="rounded-md border border-slate-200 bg-panel p-4 text-sm text-slate-500">Select a resource node.</aside>;
  }

  const visual = resourceVisual(resource.resource_type);
  const metadata = Object.entries(resource.resource_metadata).slice(0, 4);

  return (
    <aside className="rounded-md border border-slate-200 bg-panel p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{resource.resource_name}</p>
          <p className="mt-1 text-xs text-slate-500">{resource.resource_type}</p>
        </div>
        <span className="rounded-md px-2 py-1 text-xs font-semibold" style={{ backgroundColor: visual.background, color: visual.accent }}>
          {visual.label}
        </span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-md bg-white px-3 py-2">
          <p className="text-xs text-slate-500">Region</p>
          <p className="mt-1 font-semibold">{resource.region}</p>
        </div>
        <div className="rounded-md bg-white px-3 py-2">
          <p className="text-xs text-slate-500">Monthly</p>
          <p className="mt-1 font-semibold">${resource.estimated_monthly_cost}</p>
        </div>
      </div>
      <DependencyList label="Depends on" names={resource.dependencies} onSelect={onSelect} />
      <DependencyList label="Dependents" names={dependents.map((item) => item.resource_name)} onSelect={onSelect} />
      {metadata.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Metadata</p>
          <div className="mt-2 space-y-2">
            {metadata.map(([key, value]) => (
              <div className="rounded-md bg-white px-3 py-2 text-xs" key={key}>
                <p className="font-semibold text-slate-600">{key}</p>
                <p className="mt-1 truncate text-slate-500">{typeof value === "object" ? JSON.stringify(value) : String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </aside>
  );
}

function DependencyList({ label, names, onSelect }: { label: string; names: string[]; onSelect: (resourceName: string) => void }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {names.length > 0 ? (
          names.map((name) => (
            <button className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-ink" key={name} onClick={() => onSelect(name)} type="button">
              {name}
            </button>
          ))
        ) : (
          <span className="text-sm text-slate-500">None</span>
        )}
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="px-5 py-6 text-sm text-slate-500">{text}</p>;
}
