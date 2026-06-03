"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Activity, ArrowLeft, Boxes, DollarSign, GitBranch, ListChecks, RotateCcw, ShieldAlert } from "lucide-react";

import { fetchDeployment, rollbackDeployment, type Deployment } from "@/lib/api";

const TOKEN_STORAGE_KEY = "deployforge_token";

export default function DeploymentDetailPage() {
  const params = useParams<{ deploymentId: string }>();
  const router = useRouter();
  const deploymentId = params.deploymentId;
  const [deployment, setDeployment] = useState<Deployment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      router.push("/");
      return;
    }

    fetchDeployment(deploymentId, token)
      .then((result) => {
        setDeployment(result);
        setError("");
      })
      .catch(() => setError("Could not load that deployment."))
      .finally(() => setIsLoading(false));
  }, [deploymentId, router]);

  const resources = deployment?.plan.target_resources ?? [];
  const totalDependencies = useMemo(
    () => resources.reduce((sum, resource) => sum + resource.dependencies.length, 0),
    [resources],
  );

  async function handleRollback() {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!deployment || !token) {
      return;
    }

    setIsRollingBack(true);
    try {
      const result = await rollbackDeployment(deployment.id, token, "Rollback from deployment detail");
      setNotice(`Rollback created: ${result.rollback_deployment.id}`);
      setError("");
    } catch {
      setError("Could not roll back this deployment.");
    } finally {
      setIsRollingBack(false);
    }
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#f6f8fb] px-6 py-8 text-[#172033]">
        <section className="mx-auto max-w-6xl rounded-md border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-slate-500">Loading deployment...</p>
        </section>
      </main>
    );
  }

  if (!deployment) {
    return (
      <main className="min-h-screen bg-[#f6f8fb] px-6 py-8 text-[#172033]">
        <section className="mx-auto max-w-6xl rounded-md border border-slate-200 bg-white p-6 shadow-sm">
          <Link className="inline-flex items-center gap-2 text-sm font-semibold text-ink" href="/deployments">
            <ArrowLeft size={16} />
            Deployments
          </Link>
          <p className="mt-5 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {error || "Deployment not found."}
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f6f8fb] text-[#172033]">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <Link className="inline-flex items-center gap-2 text-sm font-semibold text-ink" href="/deployments">
              <ArrowLeft size={16} />
              Deployments
            </Link>
            <p className="mt-4 text-sm font-semibold uppercase tracking-wide text-signal">Deployment Detail</p>
            <h1 className="mt-2 text-3xl font-semibold">{deployment.plan.template_name}</h1>
            <p className="mt-2 text-sm text-slate-500">
              {deployment.environment} / {deployment.status} / {deployment.id}
            </p>
          </div>
          <button
            className="inline-flex h-10 w-fit items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isRollingBack}
            onClick={handleRollback}
            type="button"
          >
            <RotateCcw size={16} />
            Rollback
          </button>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          {notice ? <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</p> : null}
          {error ? <p className="rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</p> : null}

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="grid gap-4 px-5 py-5 md:grid-cols-4">
              {[
                ["Creates", deployment.plan.summary.create ?? 0],
                ["Updates", deployment.plan.summary.update ?? 0],
                ["Deletes", deployment.plan.summary.delete ?? 0],
                ["Monthly", `$${deployment.plan.estimated_monthly_cost}`],
              ].map(([label, value]) => (
                <article className="rounded-md border border-slate-200 bg-panel p-4" key={label}>
                  <p className="text-sm text-slate-500">{label}</p>
                  <p className="mt-2 text-2xl font-semibold">{value}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
              <Activity className="text-signal" size={20} />
              <h2 className="text-lg font-semibold">Pipeline Steps</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {deployment.steps.map((step) => (
                <div className="grid gap-4 px-5 py-4 md:grid-cols-[140px_1fr]" key={step.sequence_order}>
                  <div>
                    <p className="font-semibold">{step.name}</p>
                    <p className="mt-1 text-sm capitalize text-signal">{step.status}</p>
                  </div>
                  <div className="space-y-2">
                    {step.logs.map((log) => (
                      <p className="rounded-md bg-panel px-3 py-2 text-sm text-slate-600" key={log}>
                        {log}
                      </p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
              <ListChecks className="text-ink" size={20} />
              <h2 className="text-lg font-semibold">Plan Changes</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {deployment.plan.changes.map((change) => (
                <div
                  className="grid gap-3 px-5 py-4 text-sm md:grid-cols-[90px_1fr_auto]"
                  key={`${change.action}-${change.resource.name}`}
                >
                  <span className="w-fit rounded-md bg-emerald-50 px-2 py-1 font-semibold uppercase text-emerald-700">
                    {change.action}
                  </span>
                  <div>
                    <p className="font-semibold">{change.resource.name}</p>
                    <p className="mt-1 text-slate-500">{change.reason}</p>
                  </div>
                  <span className="font-semibold">${change.resource.estimated_monthly_cost}/mo</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
              <Boxes className="text-ink" size={20} />
              <h2 className="text-lg font-semibold">Resource Snapshot</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {resources.map((resource) => (
                <div className="grid gap-3 px-5 py-4 text-sm md:grid-cols-[1fr_160px_100px]" key={resource.name}>
                  <div>
                    <p className="font-semibold">{resource.name}</p>
                    <p className="mt-1 text-slate-500">
                      {resource.type} / {resource.region}
                    </p>
                  </div>
                  <span className="text-slate-600">
                    {resource.dependencies.length > 0 ? `${resource.dependencies.length} dependencies` : "root"}
                  </span>
                  <span className="font-semibold">${resource.estimated_monthly_cost}/mo</span>
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <GitBranch className="text-ink" size={20} />
              <h2 className="text-lg font-semibold">Drift</h2>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
              {Object.entries(deployment.plan.drift).map(([label, value]) => (
                <div className="rounded-md bg-panel px-3 py-2" key={label}>
                  <p className="text-xs capitalize text-slate-500">{label}</p>
                  <p className="mt-1 text-xl font-semibold">{value}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <ShieldAlert className="text-danger" size={20} />
              <h2 className="text-lg font-semibold">Policy Findings</h2>
            </div>
            <div className="mt-5 space-y-3">
              {deployment.plan.policy_violations.length > 0 ? (
                deployment.plan.policy_violations.map((violation) => (
                  <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm" key={violation.rule_id}>
                    <p className="font-semibold text-amber-950">{violation.resource_name}</p>
                    <p className="mt-1 text-amber-800">{violation.message}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No policy findings.</p>
              )}
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <DollarSign className="text-signal" size={20} />
              <h2 className="text-lg font-semibold">Snapshot Totals</h2>
            </div>
            <div className="mt-5 space-y-3 text-sm">
              <div className="flex justify-between rounded-md bg-panel px-3 py-2">
                <span>Resources</span>
                <span className="font-semibold">{resources.length}</span>
              </div>
              <div className="flex justify-between rounded-md bg-panel px-3 py-2">
                <span>Dependencies</span>
                <span className="font-semibold">{totalDependencies}</span>
              </div>
              <div className="flex justify-between rounded-md bg-panel px-3 py-2">
                <span>Monthly cost</span>
                <span className="font-semibold">${deployment.plan.estimated_monthly_cost}</span>
              </div>
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}
