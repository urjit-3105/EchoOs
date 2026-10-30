"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { authApi, type LoginPayload, type RegisterPayload } from "@/lib/api/endpoints";
import { ApiError, clearToken, getToken, setToken } from "@/lib/api/client";
import { queryKeys } from "@/lib/query-keys";
import type { User, UserRole } from "@/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<User | null>;
  register: (payload: RegisterPayload) => Promise<User | null>;
  logout: () => Promise<void>;
  requestMagicLink: (email: string) => Promise<void>;
  verifyMagicLink: (token: string) => Promise<User | null>;
  requestPasswordReset: (email: string) => Promise<void>;
  hasRole: (...roles: UserRole[]) => boolean;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();

  // Read fresh on every render (cheap cookie read) — this is what drives
  // whether the `me` query below is enabled at all, so login/logout (which
  // set/clear the cookie then update the query cache) stay in sync without
  // a manual useEffect + setState dance.
  const hasToken = !!getToken();

  const meQuery = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: async () => {
      try {
        return await authApi.me();
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          clearToken();
        }
        throw error;
      }
    },
    enabled: hasToken,
    retry: false,
  });

  const user = meQuery.data ?? null;
  const isLoading = hasToken && meQuery.isPending;

  const login = useCallback(
    async (payload: LoginPayload) => {
      try {
        const response = await authApi.login(payload);
        setToken(response.access_token);
        const me = response.user ?? (await authApi.me());
        queryClient.setQueryData(queryKeys.auth.me(), me);
        toast.success("Signed in successfully");
        return me;
      } catch (error) {
        const message = error instanceof ApiError ? error.detail : "Unable to sign in";
        toast.error(message);
        throw error;
      }
    },
    [queryClient]
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      try {
        const response = await authApi.register(payload);
        setToken(response.access_token);
        const me = response.user ?? (await authApi.me());
        queryClient.setQueryData(queryKeys.auth.me(), me);
        toast.success("Account created");
        return me;
      } catch (error) {
        const message = error instanceof ApiError ? error.detail : "Unable to register";
        toast.error(message);
        throw error;
      }
    },
    [queryClient]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore network/logout errors — always clear local state
    } finally {
      clearToken();
      queryClient.setQueryData(queryKeys.auth.me(), null);
      toast.success("Signed out");
    }
  }, [queryClient]);

  const requestMagicLink = useCallback(async (email: string) => {
    try {
      await authApi.magicLink(email);
      toast.success("Magic link sent — check your inbox");
    } catch (error) {
      const message = error instanceof ApiError ? error.detail : "Unable to send magic link";
      toast.error(message);
      throw error;
    }
  }, []);

  const verifyMagicLink = useCallback(
    async (token: string) => {
      try {
        const response = await authApi.magicLinkVerify(token);
        setToken(response.access_token);
        const me = response.user ?? (await authApi.me());
        queryClient.setQueryData(queryKeys.auth.me(), me);
        toast.success("Signed in successfully");
        return me;
      } catch (error) {
        const message = error instanceof ApiError ? error.detail : "Invalid or expired link";
        toast.error(message);
        throw error;
      }
    },
    [queryClient]
  );

  const requestPasswordReset = useCallback(async (email: string) => {
    try {
      await authApi.passwordReset(email);
      toast.success("Password reset email sent");
    } catch (error) {
      const message =
        error instanceof ApiError ? error.detail : "Unable to request password reset";
      toast.error(message);
      throw error;
    }
  }, []);

  const hasRole = useCallback(
    (...roles: UserRole[]) => (user ? roles.includes(user.role) : false),
    [user]
  );

  const refresh = useCallback(async () => {
    await meQuery.refetch();
  }, [meQuery]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
      requestMagicLink,
      verifyMagicLink,
      requestPasswordReset,
      hasRole,
      refresh,
    }),
    [
      user,
      isLoading,
      login,
      register,
      logout,
      requestMagicLink,
      verifyMagicLink,
      requestPasswordReset,
      hasRole,
      refresh,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
