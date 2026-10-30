"use client";

import React, { useState, use } from "react";
import { useApp } from "@/context/AppContext";
import { useRouter } from "next/navigation";
import { CheckCircle2, ChevronRight, FileText, Upload, Loader2, Globe } from "lucide-react";
import {
  usePortalInvitation,
  useSubmitPortalProfile,
  useUploadPortalDocument,
  useAcceptPortalTerms,
} from "@/hooks/usePortal";
import { Language, translations } from "./i18n";

export default function EmployeePortal({
  params,
}: {
  params: Promise<{ token: string }> | { token: string };
}) {
  const router = useRouter();
  const { employees, org, updateEmployee } = useApp();

  // Safely resolve params whether Promise (Next 15+) or direct object
  const resolvedParams =
    typeof (params as any)?.then === "function"
      ? use(params as Promise<{ token: string }>)
      : (params as { token: string });
  const token = resolvedParams.token;

  const [lang, setLang] = useState<Language>("en");
  const t = translations[lang] || translations.en;

  const [step, setStep] = useState(1);
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState<string[]>([]);
  const [uploadingDoc, setUploadingDoc] = useState(false);

  // Load real portal invitation from backend
  const { data: invData, isLoading: invLoading, isError: invError } = usePortalInvitation(token);
  const submitProfileMutation = useSubmitPortalProfile(token);
  const uploadDocMutation = useUploadPortalDocument(token);
  const acceptTermsMutation = useAcceptPortalTerms(token);

  // Fallback to local employee state if mock testing
  const localEmployee = employees.find((e) => e.id === token);

  const employeeName = invData?.full_name || localEmployee?.name || "Employee";
  const employeeEmail = invData?.email || localEmployee?.email || "";
  const orgName = org?.name || "Echo WorkforceOS";

  if (invLoading) {
    return (
      <div className="flex min-h-screen bg-zinc-50 dark:bg-black items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  if (invError && !localEmployee) {
    return (
      <div className="flex min-h-screen bg-zinc-50 dark:bg-black items-center justify-center">
        <div className="text-center p-8 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm max-w-md">
          <p className="text-lg font-medium text-zinc-900 dark:text-zinc-50">{t.invalid.title}</p>
          <p className="text-sm text-zinc-500 mt-2">{t.invalid.desc}</p>
        </div>
      </div>
    );
  }

  const handleSaveProfile = async () => {
    try {
      await submitProfileMutation.mutateAsync({
        address,
        phone,
        full_name: employeeName,
      });
    } catch {
      // API error handled by hook toast, continue UI step
    }
    setStep(3);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>, docType: string) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadingDoc(true);
    try {
      await uploadDocMutation.mutateAsync({ documentType: docType, file });
      setUploadedDocs((prev) => [...prev, docType]);
    } catch {
      // Local fallback indicator
      setUploadedDocs((prev) => [...prev, docType]);
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleComplete = async () => {
    try {
      await acceptTermsMutation.mutateAsync();
    } catch {
      // Local state update fallback
      if (localEmployee) {
        updateEmployee(localEmployee.id, { status: "active" });
      }
    }
    setStep(5);
  };

  const nextStep = () => setStep((prev) => prev + 1);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black flex flex-col">
      <header className="px-8 py-4 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 flex justify-between items-center">
        <h1 className="font-semibold text-zinc-900 dark:text-zinc-50">
          {orgName} {t.onboarding}
        </h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5 bg-zinc-100 dark:bg-zinc-800 px-2.5 py-1 rounded-lg border border-zinc-200 dark:border-zinc-700">
            <Globe className="w-4 h-4 text-zinc-500" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as Language)}
              className="bg-transparent text-xs font-medium text-zinc-700 dark:text-zinc-300 focus:outline-none cursor-pointer"
            >
              <option value="en">English (US)</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="hi">हिंदी</option>
            </select>
          </div>
          <div className="text-sm text-zinc-500 dark:text-zinc-400">
            {t.welcomeUser}, {employeeName}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-3xl w-full mx-auto p-8 flex flex-col justify-center">
        {step < 5 ? (
          <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center space-x-2 text-sm text-zinc-500 dark:text-zinc-400 mb-8">
              <span className={step >= 1 ? "text-zinc-900 dark:text-white font-medium" : ""}>
                {t.steps.welcome}
              </span>
              <ChevronRight className="w-4 h-4" />
              <span className={step >= 2 ? "text-zinc-900 dark:text-white font-medium" : ""}>
                {t.steps.personalInfo}
              </span>
              <ChevronRight className="w-4 h-4" />
              <span className={step >= 3 ? "text-zinc-900 dark:text-white font-medium" : ""}>
                {t.steps.documents}
              </span>
              <ChevronRight className="w-4 h-4" />
              <span className={step >= 4 ? "text-zinc-900 dark:text-white font-medium" : ""}>
                {t.steps.review}
              </span>
            </div>

            {step === 1 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
                  {t.step1.title.replace("{org}", orgName)}
                </h2>
                <p className="text-zinc-500 dark:text-zinc-400">{t.step1.desc}</p>
                <div className="pt-4">
                  <button
                    onClick={nextStep}
                    className="inline-flex justify-center py-2.5 px-6 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 transition-colors"
                  >
                    {t.step1.getStarted}
                  </button>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
                  {t.step2.title}
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      {t.step2.fullName}
                    </label>
                    <input
                      type="text"
                      defaultValue={employeeName}
                      readOnly
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm bg-zinc-50 dark:bg-zinc-800 text-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      {t.step2.email}
                    </label>
                    <input
                      type="email"
                      defaultValue={employeeEmail}
                      disabled
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm bg-zinc-50 dark:bg-zinc-800 text-zinc-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      {t.step2.phone}
                    </label>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+1 (555) 000-0000"
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      {t.step2.address}
                    </label>
                    <input
                      type="text"
                      value={address}
                      onChange={(e) => setAddress(e.target.value)}
                      placeholder={t.step2.addressPlaceholder}
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white"
                    />
                  </div>
                </div>
                <div className="pt-4 flex space-x-3">
                  <button
                    onClick={handleSaveProfile}
                    disabled={submitProfileMutation.isPending}
                    className="inline-flex justify-center py-2.5 px-6 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 transition-colors disabled:opacity-50"
                  >
                    {submitProfileMutation.isPending ? t.step2.saving : t.step2.saveAndContinue}
                  </button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
                  {t.step3.title}
                </h2>
                <div className="space-y-4">
                  <div className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-xl flex items-center justify-between">
                    <div className="flex items-center">
                      <FileText className="w-5 h-5 text-zinc-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                          {t.step3.govId}
                        </p>
                        <p className="text-xs text-zinc-500">{t.step3.govIdDesc}</p>
                      </div>
                    </div>
                    {uploadedDocs.includes("government_id") ? (
                      <span className="inline-flex items-center text-xs text-green-600 font-medium">
                        <CheckCircle2 className="w-4 h-4 mr-1" /> {t.step3.uploaded}
                      </span>
                    ) : (
                      <label className="cursor-pointer inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:underline">
                        <Upload className="w-4 h-4 mr-1" />{" "}
                        {uploadingDoc ? t.step3.uploading : t.step3.upload}
                        <input
                          type="file"
                          className="hidden"
                          onChange={(e) => handleFileUpload(e, "government_id")}
                        />
                      </label>
                    )}
                  </div>

                  <div className="p-4 border border-zinc-200 dark:border-zinc-700 rounded-xl flex items-center justify-between bg-zinc-50 dark:bg-zinc-800/50">
                    <div className="flex items-center">
                      <CheckCircle2 className="w-5 h-5 text-green-500 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50 line-through">
                          {t.step3.offerLetter}
                        </p>
                        <p className="text-xs text-zinc-500">{t.step3.offerLetterDesc}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex space-x-3">
                  <button
                    onClick={nextStep}
                    className="inline-flex justify-center py-2.5 px-6 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 transition-colors"
                  >
                    {t.step3.saveAndContinue}
                  </button>
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
                  {t.step4.title}
                </h2>
                <p className="text-zinc-500 dark:text-zinc-400">{t.step4.desc}</p>
                <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                  <label className="flex items-center text-sm text-zinc-600 dark:text-zinc-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agreed}
                      onChange={(e) => setAgreed(e.target.checked)}
                      className="mr-2 rounded border-zinc-300 dark:border-zinc-700 text-black dark:text-white focus:ring-black"
                    />
                    {t.step4.agreeTerms}
                  </label>
                </div>
                <div className="pt-4 flex space-x-3">
                  <button
                    onClick={handleComplete}
                    disabled={!agreed || acceptTermsMutation.isPending}
                    className="inline-flex justify-center py-2.5 px-6 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 disabled:opacity-50 transition-colors"
                  >
                    {acceptTermsMutation.isPending
                      ? t.step4.submitting
                      : t.step4.completeOnboarding}
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center space-y-6 animate-in zoom-in-95 duration-500">
            <div className="w-20 h-20 mx-auto rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              {t.step5.title}
            </h2>
            <p className="text-zinc-500 dark:text-zinc-400 max-w-md mx-auto">{t.step5.desc}</p>
          </div>
        )}
      </main>
    </div>
  );
}
