import { currentUser } from "@clerk/nextjs";
import { redirect } from "next/navigation";
import { DashboardNav } from "@/components/dashboard/nav";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { UsageChart } from "@/components/dashboard/usage-chart";
import { ApiKeysList } from "@/components/dashboard/api-keys-list";
import { RecentRequests } from "@/components/dashboard/recent-requests";

export default async function DashboardPage() {
  const user = await currentUser();

  if (!user) {
    redirect("/sign-in");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardNav user={user} />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">
            Welcome back, {user.firstName || user.emailAddresses[0].emailAddress}
          </h1>
          <p className="text-slate-600 mt-1">
            Monitor your AI security gateway performance and usage
          </p>
        </div>

        {/* Stats Cards */}
        <StatsCards userId={user.id} />

        {/* Usage Chart */}
        <div className="mt-8">
          <UsageChart userId={user.id} />
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mt-8">
          {/* API Keys */}
          <ApiKeysList userId={user.id} />

          {/* Recent Requests */}
          <RecentRequests userId={user.id} />
        </div>
      </main>
    </div>
  );
}
