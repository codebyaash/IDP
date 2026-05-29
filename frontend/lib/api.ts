export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Project = {
  id: string;
  name: string;
  cloud_provider: string;
  environment: string;
  status: string;
  monthly_cost: number;
  created_at: string;
};

export type ProjectCreate = {
  name: string;
  cloud_provider: string;
  environment: string;
};

export type TemplateUploadResult = {
  template: {
    id: string;
    project_id: string;
    file_name: string;
    file_type: string;
    version: number;
    created_at: string;
  };
  resources: Array<{
    name: string;
    type: string;
    provider: string;
    region: string;
    dependencies: string[];
    estimated_monthly_cost: number;
  }>;
  warnings: string[];
};

export type Resource = {
  name: string;
  type: string;
  provider: string;
  region: string;
  dependencies: string[];
  estimated_monthly_cost: number;
};

export type DeploymentPlan = {
  template_name: string;
  summary: {
    create: number;
    update: number;
    delete: number;
  };
  changes: Array<{
    action: string;
    resource: Resource;
    reason: string;
  }>;
  estimated_monthly_cost: number;
};

export type Deployment = {
  id: string;
  project_id: string;
  status: string;
  plan: DeploymentPlan;
  steps: Array<{
    name: string;
    status: string;
    logs: string[];
    sequence_order: number;
  }>;
  created_at: string | null;
};

export async function fetchProjects(): Promise<Project[]> {
  const response = await fetch(`${API_BASE_URL}/api/projects`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Unable to load projects.");
  }
  return response.json();
}

export async function createProject(payload: ProjectCreate): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Unable to create project.");
  }
  return response.json();
}

export async function uploadTemplate(projectId: string, file: File): Promise<TemplateUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/templates/upload`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error("Unable to upload template.");
  }
  return response.json();
}

export async function planTemplate(templateId: string): Promise<DeploymentPlan> {
  const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}/plan`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Unable to generate deployment plan.");
  }
  return response.json();
}

export async function deployTemplate(templateId: string): Promise<Deployment> {
  const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}/deploy`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Unable to run deployment.");
  }
  return response.json();
}

export async function fetchDeployments(projectId: string): Promise<Deployment[]> {
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/deployments`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Unable to load deployments.");
  }
  return response.json();
}
