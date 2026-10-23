import { redirect } from "next/navigation";
import { currentUser } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default async function Home() {
  const user = await currentUser();

  if (user) {
    redirect("/dashboard");
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-purple-500 rounded-lg"></div>
            <span className="text-white font-bold text-xl">Perimeter</span>
          </div>
          <div className="flex gap-4">
            <Link href="/sign-in">
              <Button variant="ghost" className="text-white">
                Sign In
              </Button>
            </Link>
            <Link href="/sign-up">
              <Button className="bg-purple-600 hover:bg-purple-700">
                Get Started
              </Button>
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl font-bold text-white mb-6">
            Enterprise AI Security
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
              Without Compromise
            </span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Perimeter provides absolute audit transparency, data compliance, and
            structural protection for external LLM integrations. Deploy frontier
            AI agents safely while guaranteeing sensitive IP never leaves your
            network boundary.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/sign-up">
              <Button size="lg" className="bg-purple-600 hover:bg-purple-700">
                Start Free Trial
              </Button>
            </Link>
            <Link href="/docs">
              <Button size="lg" variant="outline" className="text-white border-white">
                View Documentation
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-20 max-w-5xl mx-auto">
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20">
            <div className="w-12 h-12 bg-purple-500 rounded-lg mb-4 flex items-center justify-center">
              <span className="text-2xl">🔒</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Zero-Leak Security
            </h3>
            <p className="text-gray-300">
              99.95%+ automated sanitization of PII and sensitive data before
              internet egress
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20">
            <div className="w-12 h-12 bg-purple-500 rounded-lg mb-4 flex items-center justify-center">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Negative Latency
            </h3>
            <p className="text-gray-300">
              70-90% payload compression fully counterbalances security
              processing overhead
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20">
            <div className="w-12 h-12 bg-purple-500 rounded-lg mb-4 flex items-center justify-center">
              <span className="text-2xl">✅</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Type-Safe AI
            </h3>
            <p className="text-gray-300">
              BAML-powered runtime validation eliminates production downtime
              from irregular AI responses
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-8 mt-20 max-w-5xl mx-auto">
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-400 mb-2">
              99.95%
            </div>
            <div className="text-gray-300">PII Detection</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-400 mb-2">&lt;5ms</div>
            <div className="text-gray-300">Proxy Latency</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-400 mb-2">85%</div>
            <div className="text-gray-300">Avg Compression</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-400 mb-2">
              99.99%
            </div>
            <div className="text-gray-300">Uptime SLA</div>
          </div>
        </div>
      </main>
    </div>
  );
}
