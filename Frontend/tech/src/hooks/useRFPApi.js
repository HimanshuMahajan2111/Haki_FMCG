/**
 * Custom React Hooks for RFP Workflow API
 * Built on React Query for automatic caching, refetching, and state management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useRef } from 'react';
import { rfpApi, authApi, productApi, fileApi, webhookApi, systemApi } from './rfpApi';

// ==================== Authentication Hooks ====================

/**
 * Hook for user authentication
 */
export const useAuth = () => {
  const queryClient = useQueryClient();

  const loginMutation = useMutation({
    mutationFn: ({ username, password }) => authApi.login(username, password),
    onSuccess: () => {
      queryClient.invalidateQueries(['currentUser']);
    }
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.clear();
    }
  });

  const { data: currentUser, isLoading: isLoadingUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: authApi.isAuthenticated(),
    retry: false
  });

  return {
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    currentUser,
    isLoadingUser,
    isAuthenticated: authApi.isAuthenticated()
  };
};

// ==================== RFP Workflow Hooks ====================

/**
 * Hook for submitting a new RFP
 */
export const useSubmitRFP = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (rfpData) => rfpApi.submitRFP(rfpData),
    onSuccess: () => {
      // Invalidate workflows list to refetch
      queryClient.invalidateQueries(['workflows']);
    }
  });

  return {
    submitRFP: mutation.mutate,
    submitRFPAsync: mutation.mutateAsync,
    isSubmitting: mutation.isPending,
    error: mutation.error,
    data: mutation.data
  };
};

/**
 * Hook for getting workflow status with auto-refresh
 */
export const useWorkflowStatus = (workflowId, options = {}) => {
  const {
    enabled = true,
    refetchInterval = 5000, // Refetch every 5 seconds by default
    stopOnComplete = true
  } = options;

  const query = useQuery({
    queryKey: ['workflowStatus', workflowId],
    queryFn: () => rfpApi.getWorkflowStatus(workflowId),
    enabled: enabled && !!workflowId,
    refetchInterval: (data) => {
      // Stop refetching if workflow is complete or failed
      if (stopOnComplete && data && ['completed', 'failed', 'cancelled'].includes(data.status)) {
        return false;
      }
      return refetchInterval;
    }
  });

  return {
    status: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch
  };
};

/**
 * Hook for getting workflow result
 */
export const useWorkflowResult = (workflowId, options = {}) => {
  const { enabled = true } = options;

  const query = useQuery({
    queryKey: ['workflowResult', workflowId],
    queryFn: () => rfpApi.getWorkflowResult(workflowId),
    enabled: enabled && !!workflowId,
    retry: 1
  });

  return {
    result: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch
  };
};

/**
 * Hook for listing workflows with filters
 */
export const useWorkflows = (filters = {}) => {
  const query = useQuery({
    queryKey: ['workflows', filters],
    queryFn: () => rfpApi.listWorkflows(filters),
    staleTime: 10000 // Consider data fresh for 10 seconds
  });

  return {
    workflows: query.data || [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch
  };
};

/**
 * Hook for real-time workflow updates via SSE
 */
export const useWorkflowStream = (workflowId) => {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!workflowId) return;

    const handleMessage = (data) => {
      setMessages((prev) => [...prev, data]);
    };

    const handleError = (err) => {
      setError(err);
      setIsConnected(false);
    };

    setIsConnected(true);
    eventSourceRef.current = rfpApi.streamWorkflow(workflowId, handleMessage, handleError);

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [workflowId]);

  return {
    messages,
    error,
    isConnected,
    clearMessages: () => setMessages([])
  };
};

/**
 * Hook for batch RFP submission
 */
export const useBatchSubmit = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ rfps, parallel }) => rfpApi.submitBatch(rfps, parallel),
    onSuccess: () => {
      queryClient.invalidateQueries(['workflows']);
    }
  });

  return {
    submitBatch: mutation.mutate,
    isSubmitting: mutation.isPending,
    error: mutation.error,
    data: mutation.data
  };
};

// ==================== Product Hooks ====================

/**
 * Hook for searching products
 */
export const useProductSearch = () => {
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);

  const searchProducts = async (query, filters = {}) => {
    setIsSearching(true);
    setError(null);
    try {
      const results = await productApi.searchProducts(query, filters);
      setSearchResults(results);
      return results;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsSearching(false);
    }
  };

  return {
    searchProducts,
    searchResults,
    isSearching,
    error,
    clearResults: () => setSearchResults(null)
  };
};

// ==================== File Hooks ====================

/**
 * Hook for file upload
 */
export const useFileUpload = () => {
  const mutation = useMutation({
    mutationFn: ({ file, metadata }) => fileApi.uploadFile(file, metadata)
  });

  return {
    uploadFile: mutation.mutate,
    uploadFileAsync: mutation.mutateAsync,
    isUploading: mutation.isPending,
    error: mutation.error,
    uploadedFile: mutation.data,
    progress: mutation.progress // Can be enhanced with upload progress
  };
};

/**
 * Hook for file download
 */
export const useFileDownload = () => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);

  const downloadFile = async (fileId, filename = 'download') => {
    setIsDownloading(true);
    setError(null);
    try {
      const blob = await fileApi.downloadFile(fileId);
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsDownloading(false);
    }
  };

  return {
    downloadFile,
    isDownloading,
    error
  };
};

// ==================== Webhook Hooks ====================

/**
 * Hook for managing webhooks
 */
export const useWebhooks = () => {
  const queryClient = useQueryClient();

  const { data: webhooks, isLoading, error } = useQuery({
    queryKey: ['webhooks'],
    queryFn: webhookApi.listWebhooks
  });

  const registerMutation = useMutation({
    mutationFn: ({ url, events, secret }) => webhookApi.registerWebhook(url, events, secret),
    onSuccess: () => {
      queryClient.invalidateQueries(['webhooks']);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (webhookId) => webhookApi.deleteWebhook(webhookId),
    onSuccess: () => {
      queryClient.invalidateQueries(['webhooks']);
    }
  });

  return {
    webhooks: webhooks || [],
    isLoading,
    error,
    registerWebhook: registerMutation.mutate,
    deleteWebhook: deleteMutation.mutate,
    isRegistering: registerMutation.isPending,
    isDeleting: deleteMutation.isPending
  };
};

// ==================== System Hooks ====================

/**
 * Hook for system health check
 */
export const useSystemHealth = (options = {}) => {
  const { refetchInterval = 60000 } = options; // Check every minute by default

  const query = useQuery({
    queryKey: ['systemHealth'],
    queryFn: systemApi.healthCheck,
    refetchInterval
  });

  return {
    health: query.data,
    isHealthy: query.data?.status === 'healthy',
    isLoading: query.isLoading,
    error: query.error
  };
};

export default {
  useAuth,
  useSubmitRFP,
  useWorkflowStatus,
  useWorkflowResult,
  useWorkflows,
  useWorkflowStream,
  useBatchSubmit,
  useProductSearch,
  useFileUpload,
  useFileDownload,
  useWebhooks,
  useSystemHealth
};
