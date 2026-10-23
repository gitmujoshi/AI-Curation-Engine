"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { apiClient } from "@/lib/api-client";

interface UsageChartProps {
  userId: string;
}

export function UsageChart({ userId }: UsageChartProps) {
  const { data: chartData, isLoading } = useQuery({
    queryKey: ["usage-chart", userId],
    queryFn: () => apiClient.getUsageChart(userId),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-80 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="requests"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Requests"
              />
              <Line
                type="monotone"
                dataKey="tokensSaved"
                stroke="#10b981"
                strokeWidth={2}
                name="Tokens Saved"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
