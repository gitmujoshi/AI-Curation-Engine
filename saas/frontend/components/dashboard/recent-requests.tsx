"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import { formatDistanceToNow } from "date-fns";

interface RecentRequestsProps {
  userId: string;
}

export function RecentRequests({ userId }: RecentRequestsProps) {
  const { data: requests, isLoading } = useQuery({
    queryKey: ["recent-requests", userId],
    queryFn: () => apiClient.getRecentRequests(userId),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Requests</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {requests?.map((request: any) => (
              <div
                key={request.id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{request.model}</span>
                    <Badge
                      variant={
                        request.status === "success" ? "default" : "destructive"
                      }
                    >
                      {request.status}
                    </Badge>
                  </div>
                  <div className="flex gap-4 mt-1 text-xs text-slate-600">
                    <span>{request.tokens} tokens</span>
                    <span>{request.latency}ms</span>
                    <span>{request.compressionRatio}% compressed</span>
                  </div>
                </div>
                <span className="text-xs text-slate-500">
                  {formatDistanceToNow(new Date(request.timestamp), {
                    addSuffix: true,
                  })}
                </span>
              </div>
            ))}
            {(!requests || requests.length === 0) && (
              <p className="text-center text-slate-600 py-8">
                No requests yet
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
