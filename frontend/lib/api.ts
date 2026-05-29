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
