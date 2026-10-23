"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Activity,
  CreditCard,
  DollarSign,
  TrendingUp,
  Zap,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface StatsCardsProps {
  userId: string;
}

export function StatsCards({ userId }: StatsCardsProps) {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["stats", userId],
    queryFn: () => apiClient.getStats(userId),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const cards = [
    {
      title: "Total Requests",
      value: stats?.totalRequests?.toLocaleString() || "0",
      change: "+12.5%",
      icon: Activity,
      color: "text-blue-600",
    },
    {
      title: "Tokens Saved",
      value: stats?.tokensSaved?.toLocaleString() || "0",
      change: "+85.2%",
      icon: Zap,
      color: "text-purple-600",
    },
    {
      title: "Avg Compression",
      value: stats?.avgCompression || "0%",
      change: "Target: 85%",
      icon: TrendingUp,
      color: "text-green-600",
    },
    {
      title: "Monthly Cost",
      value: `$${stats?.monthlyCost?.toFixed(2) || "0.00"}`,
      change: "vs $" + (stats?.savedCost?.toFixed(2) || "0.00") + " saved",
      icon: DollarSign,
      color: "text-orange-600",
    },
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-slate-200 rounded animate-pulse" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-32 bg-slate-200 rounded animate-pulse" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {card.title}
              </CardTitle>
              <Icon className={`w-4 h-4 ${card.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
              <p className="text-xs text-slate-600 mt-1">{card.change}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
