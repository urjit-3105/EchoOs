"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { employeesApi, type EmployeeListParams } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/api/client";
import type { Employee } from "@/types";

export function useEmployees(params?: EmployeeListParams) {
  return useQuery({
    queryKey: queryKeys.employees.list(params),
    queryFn: () => employeesApi.list(params),
  });
}

export function useEmployee(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.employees.detail(id),
    queryFn: () => employeesApi.get(id),
    enabled: enabled && !!id,
  });
}

export function useEmployeeStats() {
  return useQuery({
    queryKey: queryKeys.employees.stats(),
    queryFn: employeesApi.stats,
    refetchInterval: 5000,
  });
}

export function useCreateEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Employee>) => employeesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.employees.all });
      toast.success("Employee created");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to create employee");
    },
  });
}

export function useUpdateEmployee(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Employee>) => employeesApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.employees.all });
      toast.success("Employee updated");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to update employee");
    },
  });
}

export function useDeleteEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => employeesApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.employees.all });
      toast.success("Employee removed");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to remove employee");
    },
  });
}
