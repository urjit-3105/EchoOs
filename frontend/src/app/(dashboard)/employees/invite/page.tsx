"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Mail, Check, QrCode } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateInvitation } from "@/hooks/useInvitations";
import { useInvitationQr } from "@/hooks/useInvitations";
import { DEPARTMENTS, ROLE_LABELS } from "@/constants";
import type { Invitation, UserRole } from "@/types";

const ROLE_VALUES = Object.keys(ROLE_LABELS) as UserRole[];

const inviteSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  full_name: z.string().min(1, "Full name is required"),
  department: z.string().min(1, "Select a department"),
  job_title: z.string().min(1, "Job title is required"),
  role: z.enum(["admin", "hr", "manager", "employee"]),
  message: z.string().optional(),
});

type InviteFormValues = z.infer<typeof inviteSchema>;

export default function InviteEmployee() {
  const [createdInvitation, setCreatedInvitation] = React.useState<Invitation | null>(null);
  const [isCopied, setIsCopied] = React.useState(false);

  const createInvitation = useCreateInvitation();
  const { data: qr } = useInvitationQr(createdInvitation?.id ?? "", !!createdInvitation?.id);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InviteFormValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { role: "employee" },
  });

  const inviteUrl = createdInvitation?.token
    ? `${typeof window !== "undefined" ? window.location.origin : ""}/portal/${createdInvitation.token}`
    : "";

  const onSubmit = (values: InviteFormValues) => {
    const payload: Partial<Invitation> = {
      email: values.email,
      full_name: values.full_name,
      department: values.department,
      job_title: values.job_title,
      role: values.role,
    };
    createInvitation.mutate(payload, {
      onSuccess: (invitation) => {
        setCreatedInvitation(invitation);
      },
    });
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(inviteUrl);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const sendAnother = () => {
    setCreatedInvitation(null);
    reset({ role: "employee", email: "", full_name: "", department: "", job_title: "", message: "" });
  };

  const qrSrc = qr?.qr_code
    ? qr.qr_code.startsWith("data:")
      ? qr.qr_code
      : `data:image/png;base64,${qr.qr_code}`
    : null;

  return (
    <div className="max-w-3xl animate-in fade-in duration-500">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 mb-2">
          Invite Employee
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Send an invitation to begin the automated onboarding process.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="col-span-2">
          <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6">
            <div className="flex items-center text-sm font-medium mb-6 border-b border-zinc-200 dark:border-zinc-800 pb-4 text-zinc-900 dark:text-zinc-50">
              <Mail className="w-4 h-4 mr-2" />
              Invitation Details
            </div>

            {!createdInvitation ? (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Full Name
                  </label>
                  <Input placeholder="Jane Doe" {...register("full_name")} />
                  {errors.full_name && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">{errors.full_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Email Address
                  </label>
                  <Input type="email" placeholder="jane@example.com" {...register("email")} />
                  {errors.email && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">{errors.email.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      Department
                    </label>
                    <select
                      {...register("department")}
                      defaultValue=""
                      className="w-full h-8 px-2.5 py-1 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:bg-zinc-900 text-sm text-zinc-900 dark:text-white"
                    >
                      <option value="" disabled>
                        Select department
                      </option>
                      {DEPARTMENTS.map((dept) => (
                        <option key={dept} value={dept}>
                          {dept}
                        </option>
                      ))}
                    </select>
                    {errors.department && (
                      <p className="text-xs text-red-600 dark:text-red-400 mt-1">{errors.department.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      Role
                    </label>
                    <select
                      {...register("role")}
                      className="w-full h-8 px-2.5 py-1 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:bg-zinc-900 text-sm text-zinc-900 dark:text-white"
                    >
                      {ROLE_VALUES.map((role) => (
                        <option key={role} value={role}>
                          {ROLE_LABELS[role]}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Job Title
                  </label>
                  <Input placeholder="Software Engineer" {...register("job_title")} />
                  {errors.job_title && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">{errors.job_title.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Message <span className="text-zinc-400">(optional, not sent to backend)</span>
                  </label>
                  <textarea
                    {...register("message")}
                    rows={3}
                    placeholder="Add a personal note..."
                    className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white bg-transparent dark:text-white text-sm"
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={createInvitation.isPending}
                    className="w-full sm:w-auto inline-flex justify-center py-2.5 px-6 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 focus:outline-none transition-colors disabled:opacity-50"
                  >
                    {createInvitation.isPending ? "Sending..." : "Send Invitation"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-800 dark:text-green-400">Invitation Sent!</p>
                    <p className="text-xs text-green-600 dark:text-green-500 mt-1">
                      The AI Orchestrator is tracking this invitation.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={sendAnother}
                    className="text-sm font-medium text-green-800 dark:text-green-400 hover:underline"
                  >
                    Invite Another
                  </button>
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Share Link
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      readOnly
                      value={inviteUrl}
                      className="flex-1 px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg shadow-sm bg-zinc-50 dark:bg-zinc-800 text-zinc-500 text-sm"
                    />
                    <button
                      onClick={copyToClipboard}
                      className="inline-flex justify-center items-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 transition-colors"
                    >
                      {isCopied ? <Check className="w-4 h-4" /> : "Copy"}
                    </button>
                  </div>
                </div>

                <div className="text-center py-6 border border-zinc-200 dark:border-zinc-800 rounded-xl">
                  {qrSrc ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={qrSrc} alt="Invitation QR code" className="mx-auto w-40 h-40 rounded-lg" />
                  ) : (
                    <QrCode className="w-32 h-32 text-zinc-300 dark:text-zinc-700 mx-auto" />
                  )}
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-4">
                    Scan to securely access the onboarding portal.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 h-full">
            <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-50 mb-4">What happens next?</h3>
            <ul className="space-y-4 relative">
              <li className="flex items-start">
                <div className="w-6 h-6 rounded-full bg-black dark:bg-white text-white dark:text-black flex items-center justify-center text-xs font-medium mr-3 mt-0.5">
                  1
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">Employee receives secure link</p>
              </li>
              <li className="flex items-start">
                <div className="w-6 h-6 rounded-full border border-zinc-300 dark:border-zinc-700 text-zinc-500 flex items-center justify-center text-xs font-medium mr-3 mt-0.5">
                  2
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">They complete personal details & docs</p>
              </li>
              <li className="flex items-start">
                <div className="w-6 h-6 rounded-full border border-zinc-300 dark:border-zinc-700 text-zinc-500 flex items-center justify-center text-xs font-medium mr-3 mt-0.5">
                  3
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">Verification Agent runs compliance checks</p>
              </li>
              <li className="flex items-start">
                <div className="w-6 h-6 rounded-full border border-zinc-300 dark:border-zinc-700 text-zinc-500 flex items-center justify-center text-xs font-medium mr-3 mt-0.5">
                  4
                </div>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">Execution Agent provisions accounts</p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
