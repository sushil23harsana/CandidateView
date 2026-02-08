# HireRank Frontend

Hiring manager dashboard built with Next.js (App Router), TailwindCSS, and shadcn/ui.

## Getting started

```bash
npm install
npm run dev
```

## Environment

Copy `.env.example` to `.env.local` and update values for OAuth providers and API base URL.

## Backend integration

The dashboard expects read-only endpoints:

- `GET /dashboard/jobs`
- `GET /dashboard/jobs/{job_id}/candidates`
- `GET /dashboard/jobs/{job_id}/insights`

All requests send `X-Owner-Id` derived from the authenticated session.
