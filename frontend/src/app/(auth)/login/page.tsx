"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/context/AuthContext";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const passwordSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type PasswordFormValues = z.infer<typeof passwordSchema>;

const DEMO_ADMIN_EMAIL = "admin@echo-workforceos.com";
const DEMO_ADMIN_PASSWORD = "EchoDemo123!";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading…</p>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, requestMagicLink, verifyMagicLink, requestPasswordReset } =
    useAuth();

  const [magicLinkEmail, setMagicLinkEmail] = useState("");
  const [magicLinkLoading, setMagicLinkLoading] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);

  const [verifyingToken, setVerifyingToken] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);

  const [demoLoading, setDemoLoading] = useState(false);

  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState("");
  const [forgotPasswordLoading, setForgotPasswordLoading] = useState(false);
  const [forgotPasswordSent, setForgotPasswordSent] = useState(false);

  const [formError, setFormError] = useState<string | null>(null);

  const {
    register: registerField,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { email: "", password: "" },
  });

  // Nice-to-have: bounce straight to the dashboard if already signed in.
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  // Handle ?token= magic-link verification on mount.
  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) return;

    let cancelled = false;
    setVerifyingToken(true);
    setTokenError(null);

    verifyMagicLink(token)
      .then(() => {
        if (cancelled) return;
        router.replace("/login");
        router.push("/dashboard");
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setTokenError(
          error instanceof Error ? error.message : "That magic link is invalid or expired."
        );
      })
      .finally(() => {
        if (!cancelled) setVerifyingToken(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const onPasswordSubmit = async (values: PasswordFormValues) => {
    setFormError(null);
    try {
      await login(values);
      router.push("/dashboard");
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Unable to sign in");
    }
  };

  const handleMagicLinkRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!magicLinkEmail) return;
    setMagicLinkLoading(true);
    try {
      await requestMagicLink(magicLinkEmail);
      setMagicLinkSent(true);
    } catch {
      // requestMagicLink already toasts the error
    } finally {
      setMagicLinkLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotPasswordEmail) return;
    setForgotPasswordLoading(true);
    try {
      await requestPasswordReset(forgotPasswordEmail);
      setForgotPasswordSent(true);
    } catch {
      // requestPasswordReset already toasts the error
    } finally {
      setForgotPasswordLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setFormError(null);
    setDemoLoading(true);
    try {
      await login({ email: DEMO_ADMIN_EMAIL, password: DEMO_ADMIN_PASSWORD });
      router.push("/dashboard");
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Unable to sign in as demo admin");
    } finally {
      setDemoLoading(false);
    }
  };

  if (verifyingToken) {
    return (
      <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">Verifying your magic link…</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 mb-2">
          Welcome to ECHO
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Sign in to your autonomous workforce OS
        </p>
      </div>

      {tokenError && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-400">
          {tokenError}
        </div>
      )}

      {forgotPasswordOpen ? (
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Reset your password
          </h2>
          {forgotPasswordSent ? (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              If an account exists for that email, a reset link is on its way — check your inbox.
            </p>
          ) : (
            <form onSubmit={handleForgotPassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Email address
                </label>
                <Input
                  type="email"
                  required
                  value={forgotPasswordEmail}
                  onChange={(e) => setForgotPasswordEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="h-10"
                />
              </div>
              <Button type="submit" disabled={forgotPasswordLoading} className="w-full h-10">
                {forgotPasswordLoading ? "Sending…" : "Send reset link"}
              </Button>
            </form>
          )}
          <button
            type="button"
            onClick={() => {
              setForgotPasswordOpen(false);
              setForgotPasswordSent(false);
            }}
            className="text-sm text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white underline underline-offset-4"
          >
            Back to sign in
          </button>
        </div>
      ) : (
        <Tabs defaultValue="password">
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="password">Password</TabsTrigger>
            <TabsTrigger value="magic-link">Magic Link</TabsTrigger>
          </TabsList>

          <TabsContent value="password" className="mt-6">
            <form onSubmit={handleSubmit(onPasswordSubmit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Email address
                </label>
                <Input
                  type="email"
                  placeholder="you@company.com"
                  className="h-10"
                  {...registerField("email")}
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setForgotPasswordOpen(true)}
                    className="text-xs text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white underline underline-offset-4"
                  >
                    Forgot password?
                  </button>
                </div>
                <Input
                  type="password"
                  placeholder="••••••••"
                  className="h-10"
                  {...registerField("password")}
                />
                {errors.password && (
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                    {errors.password.message}
                  </p>
                )}
              </div>

              {formError && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-400">
                  {formError}
                </div>
              )}

              <Button type="submit" disabled={isSubmitting} className="w-full h-10">
                {isSubmitting ? "Signing in…" : "Sign in"}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="magic-link" className="mt-6">
            {magicLinkSent ? (
              <p className="text-sm text-zinc-500 dark:text-zinc-400 text-center py-4">
                Check your inbox — we sent a sign-in link to{" "}
                <span className="font-medium text-zinc-900 dark:text-zinc-100">
                  {magicLinkEmail}
                </span>
                .
              </p>
            ) : (
              <form onSubmit={handleMagicLinkRequest} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Email address
                  </label>
                  <Input
                    type="email"
                    required
                    value={magicLinkEmail}
                    onChange={(e) => setMagicLinkEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="h-10"
                  />
                </div>
                <Button type="submit" disabled={magicLinkLoading} className="w-full h-10">
                  {magicLinkLoading ? "Sending…" : "Email me a magic link"}
                </Button>
              </form>
            )}
          </TabsContent>
        </Tabs>
      )}

      <div className="mt-6">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-200 dark:border-zinc-700" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white dark:bg-zinc-900 text-zinc-500">
              For evaluators
            </span>
          </div>
        </div>

        <div className="mt-6">
          <Button
            type="button"
            variant="outline"
            disabled={demoLoading}
            onClick={handleDemoLogin}
            className="w-full h-10"
          >
            {demoLoading ? "Signing in…" : "Sign in as demo admin"}
          </Button>
          <p className="mt-2 text-center text-xs text-zinc-400 dark:text-zinc-500">
            Judge shortcut — skips the form with seeded demo admin credentials
          </p>
        </div>
      </div>
    </div>
  );
}
