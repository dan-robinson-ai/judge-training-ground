"use client";

import { useState } from "react";
import { useTrainingStore } from "@/lib/store";
import { Run } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  History,
  Eye,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";

function getAccuracyColor(accuracy: number) {
  if (accuracy >= 90) return "text-[#30a46c]";
  if (accuracy >= 70) return "text-[#f5a623]";
  return "text-[#e5484d]";
}

export function RunHistoryView() {
  const { runs, promptVersions, testCases, isRunning } = useTrainingStore();
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);

  // Loading state
  if (isRunning) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center p-8">
        <div className="relative">
          <div className="h-12 w-12 rounded-full border-4 border-secondary border-t-primary animate-spin" />
        </div>
        <div>
          <h3 className="font-medium text-foreground">Running Evaluation</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Evaluating {testCases.length} test cases...
          </p>
        </div>
      </div>
    );
  }

  // Empty state
  if (runs.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center p-8">
        <div className="rounded-full bg-secondary p-4">
          <History className="h-8 w-8 text-muted-foreground" />
        </div>
        <div>
          <h3 className="font-medium text-foreground">No runs yet</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Run an evaluation to see the history here
          </p>
        </div>
      </div>
    );
  }

  // Build version lookup
  const versionLookup = Object.fromEntries(
    promptVersions.map((v) => [v.id, v])
  );

  // Sort runs by date descending
  const sortedRuns = [...runs].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  return (
    <div className="flex h-full flex-col">
      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 p-4 border-b border-border">
        <div className="text-center">
          <div className="text-2xl font-bold text-foreground">{runs.length}</div>
          <div className="text-xs text-muted-foreground">Total Runs</div>
        </div>
        <div className="text-center">
          <div
            className={`text-2xl font-bold ${getAccuracyColor(
              Math.max(...runs.map((r) => r.stats.accuracy))
            )}`}
          >
            {Math.max(...runs.map((r) => r.stats.accuracy)).toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground">Best Accuracy</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-foreground">
            {Math.max(...runs.map((r) => r.stats.cohen_kappa)).toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground">Best Cohen k</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-foreground">
            {new Set(runs.map((r) => r.modelName)).size}
          </div>
          <div className="text-xs text-muted-foreground">Models Used</div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="w-[15%]">Date</TableHead>
              <TableHead className="w-[15%]">Version</TableHead>
              <TableHead className="w-[15%]">Model</TableHead>
              <TableHead className="w-[12%] text-center">Accuracy</TableHead>
              <TableHead className="w-[12%] text-center">Cohen k</TableHead>
              <TableHead className="w-[8%] text-center">Correct</TableHead>
              <TableHead className="w-[8%] text-center">Wrong</TableHead>
              <TableHead className="w-[8%] text-center">Errors</TableHead>
              <TableHead className="w-[7%] text-right">Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedRuns.map((run) => {
              const version = versionLookup[run.promptVersionId];

              return (
                <TableRow
                  key={run.id}
                  className="border-border hover:bg-secondary/50"
                >
                  <TableCell className="text-sm">
                    {new Date(run.createdAt).toLocaleDateString()}
                    <br />
                    <span className="text-xs text-muted-foreground">
                      {new Date(run.createdAt).toLocaleTimeString()}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">v{version?.version ?? "?"}</Badge>
                      <Badge variant="secondary" className="text-xs capitalize">
                        {version?.source ?? "unknown"}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{run.modelName}</span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`font-bold ${getAccuracyColor(
                        run.stats.accuracy
                      )}`}
                    >
                      {run.stats.accuracy.toFixed(1)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className="font-medium">
                      {run.stats.cohen_kappa.toFixed(2)}
                    </span>
                  </TableCell>
                  <TableCell className="text-center text-[#30a46c] font-medium">
                    {run.stats.passed}
                  </TableCell>
                  <TableCell className="text-center text-[#e5484d] font-medium">
                    {run.stats.failed}
                  </TableCell>
                  <TableCell className="text-center text-[#f5a623] font-medium">
                    {run.stats.errors}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setSelectedRun(run)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Run Details Dialog */}
      <RunDetailsDialog run={selectedRun} onClose={() => setSelectedRun(null)} />
    </div>
  );
}

// Separate component for run details modal
function RunDetailsDialog({
  run,
  onClose,
}: {
  run: Run | null;
  onClose: () => void;
}) {
  const { testCases } = useTrainingStore();

  if (!run) return null;

  const testCaseLookup = Object.fromEntries(testCases.map((tc) => [tc.id, tc]));

  return (
    <Dialog open={!!run} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            Run Details - {new Date(run.createdAt).toLocaleString()}
          </DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[5%]"></TableHead>
                <TableHead className="w-[40%]">Input</TableHead>
                <TableHead className="w-[10%]">Expected</TableHead>
                <TableHead className="w-[10%]">Actual</TableHead>
                <TableHead className="w-[35%]">Reasoning</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {run.stats.results.map((result) => {
                const testCase = testCaseLookup[result.test_case_id];
                const isCorrect = result.correct;
                const isError = result.actual_verdict === "ERROR";

                return (
                  <TableRow
                    key={result.test_case_id}
                    className={
                      isError
                        ? "bg-[#f5a623]/5"
                        : !isCorrect
                        ? "bg-[#e5484d]/5"
                        : ""
                    }
                  >
                    <TableCell>
                      {isError ? (
                        <AlertCircle className="h-5 w-5 text-[#f5a623]" />
                      ) : isCorrect ? (
                        <CheckCircle className="h-5 w-5 text-[#30a46c]" />
                      ) : (
                        <XCircle className="h-5 w-5 text-[#e5484d]" />
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      <div
                        className="truncate max-w-xs"
                        title={testCase?.input_text}
                      >
                        {testCase?.input_text || "Unknown"}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          testCase?.expected_verdict === "PASS"
                            ? "border-[#30a46c] text-[#30a46c]"
                            : "border-[#e5484d] text-[#e5484d]"
                        }
                      >
                        {testCase?.expected_verdict || "?"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          isError
                            ? "border-[#f5a623] text-[#f5a623]"
                            : result.actual_verdict === "PASS"
                            ? "border-[#30a46c] text-[#30a46c]"
                            : "border-[#e5484d] text-[#e5484d]"
                        }
                      >
                        {result.actual_verdict}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      <div
                        className="truncate max-w-xs"
                        title={result.reasoning}
                      >
                        {result.reasoning}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </DialogContent>
    </Dialog>
  );
}
