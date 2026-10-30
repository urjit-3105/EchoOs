"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { LoadingState } from "@/components/LoadingState";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ROLE_LABELS } from "@/constants";
import { initials, formatDate } from "@/utils/format";

export default function ProfilePage() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name ?? "");

  if (!user) {
    return (
      <div className="p-8">
        <LoadingState variant="card" rows={2} />
      </div>
    );
  }

  // NOTE: there is no update-profile endpoint exposed in src/lib/api/endpoints.ts
  // (no authApi.updateMe / usersApi.update). Rather than fake persistence, the
  // edit form stays local-only and surfaces an honest "not available yet" toast
  // on save instead of pretending the change was stored.
  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    toast.error("Profile editing isn't available yet");
    setIsEditing(false);
    setFullName(user.full_name ?? "");
  };

  const handleCancel = () => {
    setFullName(user.full_name ?? "");
    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Profile
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Your account details and role within the organization.
        </p>
      </div>

      <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8">
        <div className="flex items-start gap-4">
          <Avatar size="lg">
            {user.avatar_url && <AvatarImage src={user.avatar_url} alt={user.full_name ?? user.email} />}
            <AvatarFallback>{initials(user.full_name ?? user.email)}</AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
              {user.full_name ?? "Unnamed User"}
            </h2>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">{user.email}</p>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant="outline">{ROLE_LABELS[user.role]}</Badge>
              {user.is_active === false && <Badge variant="destructive">Inactive</Badge>}
            </div>
          </div>
        </div>

        <div className="mt-8 border-t border-zinc-200 dark:border-zinc-800 pt-6">
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Full name
              </label>
              <Input
                value={fullName}
                disabled={!isEditing}
                onChange={(e) => setFullName(e.target.value)}
                className="h-10 max-w-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Email
              </label>
              <Input value={user.email} disabled className="h-10 max-w-sm" />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Member since
              </label>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {formatDate(user.created_at)}
              </p>
            </div>

            <div className="flex gap-3 pt-2">
              {isEditing ? (
                <>
                  <Button type="submit">Save changes</Button>
                  <Button type="button" variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                </>
              ) : (
                <Button type="button" variant="outline" onClick={() => setIsEditing(true)}>
                  Edit profile
                </Button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
