"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Eye, EyeOff, Plus, Trash2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "@/lib/toast";

interface ApiKeysListProps {
  userId: string;
}

export function ApiKeysList({ userId }: ApiKeysListProps) {
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["api-keys", userId],
    queryFn: () => apiClient.getApiKeys(userId),
  });

  const createKeyMutation = useMutation({
    mutationFn: () => apiClient.createApiKey(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys", userId] });
      toast.success("API key created successfully");
    },
  });

  const deleteKeyMutation = useMutation({
    mutationFn: (keyId: string) => apiClient.deleteApiKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys", userId] });
      toast.success("API key deleted");
    },
  });

  const toggleVisibility = (keyId: string) => {
    setVisibleKeys((prev) => {
      const next = new Set(prev);
      if (next.has(keyId)) {
        next.delete(keyId);
      } else {
        next.add(keyId);
      }
      return next;
    });
  };

  const copyToClipboard = (key: string) => {
    navigator.clipboard.writeText(key);
    toast.success("Copied to clipboard");
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>API Keys</CardTitle>
        <Button
          size="sm"
          onClick={() => createKeyMutation.mutate()}
          disabled={createKeyMutation.isPending}
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Key
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {apiKeys?.map((apiKey: any) => (
              <div
                key={apiKey.id}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <code className="text-sm font-mono">
                      {visibleKeys.has(apiKey.id)
                        ? apiKey.key
                        : apiKey.key.slice(0, 20) + "..."}
                    </code>
                    <Badge variant={apiKey.active ? "default" : "secondary"}>
                      {apiKey.active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">
                    Created {new Date(apiKey.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => toggleVisibility(apiKey.id)}
                  >
                    {visibleKeys.has(apiKey.id) ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(apiKey.key)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => deleteKeyMutation.mutate(apiKey.id)}
                    disabled={deleteKeyMutation.isPending}
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </Button>
                </div>
              </div>
            ))}
            {(!apiKeys || apiKeys.length === 0) && (
              <p className="text-center text-slate-600 py-8">
                No API keys yet. Create one to get started.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
