"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { CheckCircle2, CircleDashed } from "lucide-react";

const steps = [
  "Creating Organization...",
  "Initializing Database...",
  "Configuring Security...",
  "Preparing AI Workspace...",
  "Finalizing...",
];

export default function InitWorkspace() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // If the user never made it through setup (no session), bounce back.
    if (!isLoading && !isAuthenticated) {
      router.push("/setup");
      return;
    }

    if (isLoading || !isAuthenticated) return;

    let isMounted = true;

    const runSteps = async () => {
      for (let i = 0; i < steps.length; i++) {
        if (!isMounted) return;
        setCurrentStep(i);
        // Random wait between 800ms and 1500ms
        await new Promise((r) => setTimeout(r, Math.random() * 700 + 800));
      }

      if (isMounted) {
        // Done, redirect to dashboard
        router.push("/dashboard");
      }
    };

    runSteps();

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-10 max-w-md mx-auto w-full">
      <div className="text-center mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 mb-2">
          Initializing Workspace
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Please wait while we set up your environment.
        </p>
      </div>

      <div className="space-y-6">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isPending = index > currentStep;

          return (
            <div key={step} className={`flex items-center space-x-4 transition-opacity duration-300 ${isPending ? 'opacity-40' : 'opacity-100'}`}>
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <CheckCircle2 className="w-6 h-6 text-black dark:text-white" />
                ) : isCurrent ? (
                  <CircleDashed className="w-6 h-6 text-zinc-400 dark:text-zinc-500 animate-spin" />
                ) : (
                  <div className="w-6 h-6 rounded-full border-2 border-zinc-200 dark:border-zinc-800" />
                )}
              </div>
              <div className="flex-1">
                <p className={`text-sm font-medium ${isCurrent ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 dark:text-zinc-400'}`}>
                  {step}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
