"use client";

import { signIn } from "next-auth/react";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-muted/40 flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to HireRank</CardTitle>
          <CardDescription>
            Access the hiring manager dashboard to review ranked candidates.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            className="w-full"
            onClick={() => signIn("google", { callbackUrl: "/jobs" })}
          >
            Continue with Google
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => signIn("github", { callbackUrl: "/jobs" })}
          >
            Continue with GitHub
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
          <p className="text-xs text-muted-foreground">
            OAuth credentials are configured via environment variables. For demo
            environments, use mocked providers or set GITHUB_ID/SECRET and
            GOOGLE_CLIENT_ID/SECRET.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
