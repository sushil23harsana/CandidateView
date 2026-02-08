"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, RefreshCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import type { JobSummary } from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.API_BASE_URL ??
  "http://localhost:8000";

const FIELD_OPTIONS = [
  { value: "", label: "Ignore column" },
  { value: "name", label: "Candidate name" },
  { value: "email", label: "Candidate email" },
  { value: "github_url", label: "GitHub URL" },
  { value: "resume_url", label: "Resume URL" },
  { value: "skills", label: "Skills" },
  { value: "status", label: "Status" },
  { value: "experience_years", label: "Experience years" },
  { value: "required_experience_years", label: "Required experience years" }
];

const REQUIRED_FIELDS = ["name", "email"];

type PreviewResponse = {
  headers: string[];
  rows: Record<string, string>[];
};

type ImportResult = {
  row_number: number;
  status: string;
  candidate_id?: string | null;
  errors?: string[];
};

type ImportJob = {
  import_id: string;
  status: string;
  total_rows: number;
  processed_rows: number;
  success_count: number;
  failure_count: number;
  results: ImportResult[];
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

type ImportCsvProps = {
  ownerId: string;
  jobs: JobSummary[];
};

function guessField(header: string): string {
  const normalized = header.trim().toLowerCase();
  if (["name", "full name", "candidate name"].includes(normalized)) {
    return "name";
  }
  if (["email", "email address"].includes(normalized)) {
    return "email";
  }
  if (["github", "github url", "github profile"].includes(normalized)) {
    return "github_url";
  }
  if (["resume", "resume url", "cv", "cv url"].includes(normalized)) {
    return "resume_url";
  }
  if (["skills", "skill"].includes(normalized)) {
    return "skills";
  }
  if (["status", "application status"].includes(normalized)) {
    return "status";
  }
  if (["experience", "experience years", "years"].includes(normalized)) {
    return "experience_years";
  }
  if (
    [
      "required experience",
      "required experience years",
      "required years",
      "required_experience_years"
    ].includes(normalized)
  ) {
    return "required_experience_years";
  }
  return "";
}

function formatFieldLabel(value: string) {
  return FIELD_OPTIONS.find((option) => option.value === value)?.label ?? value;
}

export function ImportCsv({ ownerId, jobs }: ImportCsvProps) {
  const [selectedJobId, setSelectedJobId] = useState(jobs[0]?.id ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [importJob, setImportJob] = useState<ImportJob | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const missingRequiredFields = useMemo(() => {
    const fieldsSelected = new Set(Object.values(mapping).filter(Boolean));
    return REQUIRED_FIELDS.filter((field) => !fieldsSelected.has(field));
  }, [mapping]);

  const chosenFields = useMemo(
    () => new Set(Object.values(mapping).filter(Boolean)),
    [mapping]
  );

  useEffect(() => {
    if (!importJob) {
      return;
    }
    if (!["queued", "processing"].includes(importJob.status)) {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/dashboard/jobs/${selectedJobId}/imports/${importJob.import_id}`,
          {
            headers: {
              "Content-Type": "application/json",
              "X-Owner-Id": ownerId
            }
          }
        );
        if (!response.ok) {
          throw new Error("Failed to fetch import status");
        }
        const payload = (await response.json()) as ImportJob;
        setImportJob(payload);
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : "Unable to load import status."
        );
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [importJob, ownerId, selectedJobId]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newFile = event.target.files?.[0] ?? null;
    setFile(newFile);
    setPreview(null);
    setMapping({});
    setImportJob(null);
    setErrorMessage(null);
  };

  const handlePreview = async () => {
    if (!file || !selectedJobId) {
      setErrorMessage("Select a job and CSV file before previewing.");
      return;
    }
    setIsPreviewing(true);
    setErrorMessage(null);
    setImportJob(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_BASE_URL}/dashboard/jobs/${selectedJobId}/imports/preview`,
        {
          method: "POST",
          headers: {
            "X-Owner-Id": ownerId
          },
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error("Preview failed. Check the CSV file format.");
      }

      const payload = (await response.json()) as PreviewResponse;
      setPreview(payload);
      const guessedMapping: Record<string, string> = {};
      payload.headers.forEach((header) => {
        guessedMapping[header] = guessField(header);
      });
      setMapping(guessedMapping);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Preview request failed."
      );
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleMappingChange = (header: string, field: string) => {
    setMapping((current) => ({
      ...current,
      [header]: field
    }));
  };

  const handleStartImport = async () => {
    if (!file || !selectedJobId) {
      setErrorMessage("Select a job and CSV file before starting the import.");
      return;
    }
    if (missingRequiredFields.length > 0) {
      setErrorMessage(
        `Map the required fields: ${missingRequiredFields.join(", ")}.`
      );
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const mappingPayload: Record<string, string> = {};
      Object.entries(mapping).forEach(([column, field]) => {
        if (field) {
          mappingPayload[field] = column;
        }
      });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("mapping", JSON.stringify(mappingPayload));

      const response = await fetch(
        `${API_BASE_URL}/dashboard/jobs/${selectedJobId}/imports`,
        {
          method: "POST",
          headers: {
            "X-Owner-Id": ownerId
          },
          body: formData
        }
      );

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to start import.");
      }

      const payload = (await response.json()) as ImportJob;
      setImportJob(payload);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Import failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Import CSV</h2>
          <p className="text-sm text-muted-foreground">
            Upload candidate data, map columns, and track import progress.
          </p>
        </div>
        {preview && (
          <Badge variant="outline">
            {preview.rows.length} preview rows
          </Badge>
        )}
      </div>

      {jobs.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No jobs available</CardTitle>
            <CardDescription>
              Create a job before importing candidates via CSV.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Upload CSV</CardTitle>
            <CardDescription>
              Choose a job, upload a CSV, then preview and map columns.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-[200px_1fr]">
              <label className="text-sm font-medium" htmlFor="job-select">
                Job
              </label>
              <select
                id="job-select"
                className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                value={selectedJobId}
                onChange={(event) => setSelectedJobId(event.target.value)}
              >
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title} ({job.id})
                  </option>
                ))}
              </select>

              <label className="text-sm font-medium" htmlFor="csv-input">
                CSV file
              </label>
              <input
                id="csv-input"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full text-sm"
              />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={handlePreview} disabled={isPreviewing || !file}>
                {isPreviewing ? "Previewing..." : "Preview CSV"}
              </Button>
              <Button
                variant="outline"
                onClick={handleStartImport}
                disabled={!preview || isSubmitting}
              >
                {isSubmitting ? "Starting import..." : "Start import"}
              </Button>
            </div>

            {missingRequiredFields.length > 0 && preview && (
              <p className="text-sm text-muted-foreground">
                Required fields still needed: {missingRequiredFields.join(", ")}.
              </p>
            )}

            {errorMessage && (
              <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                {errorMessage}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>Preview &amp; map columns</CardTitle>
            <CardDescription>
              Match each CSV column to a candidate field.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {preview.headers.map((header) => (
                <div
                  key={header}
                  className="grid gap-3 rounded-md border border-border px-4 py-3 md:grid-cols-[1fr_220px]"
                >
                  <div>
                    <p className="text-sm font-medium">{header}</p>
                    <p className="text-xs text-muted-foreground">
                      Sample: {preview.rows[0]?.[header] ?? "—"}
                    </p>
                  </div>
                  <select
                    className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                    value={mapping[header] ?? ""}
                    onChange={(event) =>
                      handleMappingChange(header, event.target.value)
                    }
                  >
                    {FIELD_OPTIONS.map((option) => (
                      <option
                        key={option.value || "ignore"}
                        value={option.value}
                        disabled={
                          option.value !== "" &&
                          option.value !== mapping[header] &&
                          chosenFields.has(option.value)
                        }
                      >
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  {preview.headers.map((header) => (
                    <TableHead key={header}>{header}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {preview.rows.map((row, index) => (
                  <TableRow key={index}>
                    {preview.headers.map((header) => (
                      <TableCell key={header}>{row[header] || "—"}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {importJob && (
        <Card>
          <CardHeader>
            <CardTitle>Import status</CardTitle>
            <CardDescription>
              {importJob.status === "completed"
                ? "Import finished. Review the per-row summary below."
                : "Import in progress. This view refreshes automatically."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <Badge variant="outline">Status: {importJob.status}</Badge>
              <span>
                Processed {importJob.processed_rows} of {importJob.total_rows}
              </span>
              <span className="text-emerald-600">
                Success: {importJob.success_count}
              </span>
              <span className="text-destructive">
                Failed: {importJob.failure_count}
              </span>
              {["queued", "processing"].includes(importJob.status) && (
                <span className="inline-flex items-center gap-1 text-muted-foreground">
                  <RefreshCcw className="h-3 w-3 animate-spin" /> Refreshing
                </span>
              )}
            </div>

            {importJob.error_message && (
              <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                {importJob.error_message}
              </div>
            )}

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Row</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {importJob.results.map((result) => (
                  <TableRow key={result.row_number}>
                    <TableCell>{result.row_number}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center gap-1">
                        {result.status === "success" ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-destructive" />
                        )}
                        {result.status}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {result.status === "success"
                        ? result.candidate_id
                          ? `Candidate ID: ${result.candidate_id}`
                          : "Imported"
                        : result.errors?.join(" ") || "Unknown error"}
                    </TableCell>
                  </TableRow>
                ))}
                {importJob.results.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} className="text-sm text-muted-foreground">
                      No rows processed yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {preview && (
        <Card className="border-dashed">
          <CardHeader>
            <CardTitle>Mapping summary</CardTitle>
            <CardDescription>
              {Object.values(mapping).filter(Boolean).length} mapped fields.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {Object.entries(mapping)
              .filter(([, field]) => field)
              .map(([column, field]) => (
                <div key={column} className="flex items-center justify-between">
                  <span className="font-medium">{column}</span>
                  <span className="text-muted-foreground">
                    {formatFieldLabel(field)}
                  </span>
                </div>
              ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
