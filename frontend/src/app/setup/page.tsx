"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useCreateOrganization } from "@/hooks/useOrganizations";

interface SetupFormData {
  name: string;
  industry: string;
  size: string;
  adminEmail: string;
  adminPassword: string;
}

export default function SetupWizard() {
  const router = useRouter();
  const { register } = useAuth();
  const createOrganization = useCreateOrganization();

  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [formData, setFormData] = useState<SetupFormData>({
    name: "",
    industry: "",
    size: "",
    adminEmail: "",
    adminPassword: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleNext = () => setStep((prev) => prev + 1);
  const handleBack = () => setStep((prev) => prev - 1);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);
    try {
      // There is no dedicated "create org + first admin" bootstrap endpoint on
      // the backend, so we sequence two real calls: first create the
      // organization record (name/industry/size), then register the first
      // admin user, passing `organization_name` so the backend can associate
      // the new user with the org we just created. `register` already signs
      // the admin in (stores the token + populates the auth/me cache).
      await createOrganization.mutateAsync({
        name: formData.name,
        industry: formData.industry,
        size: formData.size,
      });

      await register({
        email: formData.adminEmail,
        password: formData.adminPassword,
        full_name: "Admin",
        organization_name: formData.name,
      });

      router.push("/setup/init");
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Something went wrong setting up your workspace"
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 mb-2">
          Create Organization
        </h1>
        <div className="w-full bg-zinc-200 dark:bg-zinc-800 rounded-full h-1.5 mb-4 mt-6">
          <div
            className="bg-black dark:bg-white h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${(step / 3) * 100}%` }}
          ></div>
        </div>
      </div>

      <form onSubmit={step === 3 ? handleSubmit : (e) => { e.preventDefault(); handleNext(); }}>
        {step === 1 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Organization Name
              </label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white"
                placeholder="Acme Corp"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Industry
              </label>
              <select
                name="industry"
                required
                value={formData.industry}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white"
              >
                <option value="" disabled>Select an industry</option>
                <option value="Technology">Technology</option>
                <option value="Finance">Finance</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Company Size
              </label>
              <select
                name="size"
                required
                value={formData.size}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white"
              >
                <option value="" disabled>Select size</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201+">201+ employees</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Admin Email
              </label>
              <input
                type="email"
                name="adminEmail"
                required
                value={formData.adminEmail}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Admin Password
              </label>
              <input
                type="password"
                name="adminPassword"
                required
                minLength={8}
                value={formData.adminPassword}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white"
                placeholder="At least 8 characters"
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 divide-y divide-zinc-200 dark:divide-zinc-800 text-sm">
              <div className="flex justify-between px-3 py-2">
                <span className="text-zinc-500 dark:text-zinc-400">Organization</span>
                <span className="font-medium text-zinc-900 dark:text-zinc-50">{formData.name || "—"}</span>
              </div>
              <div className="flex justify-between px-3 py-2">
                <span className="text-zinc-500 dark:text-zinc-400">Industry</span>
                <span className="font-medium text-zinc-900 dark:text-zinc-50">{formData.industry || "—"}</span>
              </div>
              <div className="flex justify-between px-3 py-2">
                <span className="text-zinc-500 dark:text-zinc-400">Size</span>
                <span className="font-medium text-zinc-900 dark:text-zinc-50">{formData.size || "—"}</span>
              </div>
              <div className="flex justify-between px-3 py-2">
                <span className="text-zinc-500 dark:text-zinc-400">Admin</span>
                <span className="font-medium text-zinc-900 dark:text-zinc-50">{formData.adminEmail || "—"}</span>
              </div>
            </div>
            {submitError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-400">
                {submitError}
              </div>
            )}
            <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-4">
              By clicking &quot;Initialize Workspace&quot;, you agree to the Terms of Service.
            </p>
          </div>
        )}

        <div className="mt-8 flex justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={handleBack}
              disabled={submitting}
              className="py-2.5 px-4 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black transition-colors disabled:opacity-50"
            >
              Back
            </button>
          ) : (
            <div></div> // Empty div to push 'Next' button to the right
          )}
          <button
            type="submit"
            disabled={submitting}
            className="py-2.5 px-6 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black transition-colors disabled:opacity-50"
          >
            {step === 3 ? (submitting ? "Initializing…" : "Initialize Workspace") : "Continue"}
          </button>
        </div>
      </form>
    </div>
  );
}
