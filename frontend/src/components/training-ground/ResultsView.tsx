"use client";

import { useTrainingStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CheckCircle, XCircle, AlertCircle, TrendingUp } from "lucide-react";

export function ResultsView() {
  const { testCases, runStats, isRunning } = useTrainingStore();

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

  if (!runStats) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center p-8">
        <div className="rounded-full bg-secondary p-4">
          <TrendingUp className="h-8 w-8 text-muted-foreground" />
        </div>
        <div>
          <h3 className="font-medium text-foreground">No results yet</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Run an evaluation to see the results here
          </p>
        </div>
      </div>
    );
  }

  const testCaseLookup = Object.fromEntries(
    testCases.map((tc) => [tc.id, tc])
  );

  const accuracyColor =
    runStats.accuracy >= 90
      ? "text-[#30a46c]"
      : runStats.accuracy >= 70
      ? "text-[#f5a623]"
      : "text-[#e5484d]";

  // Cohen's Kappa interpretation
  const getKappaInfo = (kappa: number) => {
    if (kappa >= 0.81) return { label: "Almost Perfect", color: "text-[#30a46c]" };
    if (kappa >= 0.61) return { label: "Substantial", color: "text-[#30a46c]" };
    if (kappa >= 0.41) return { label: "Moderate", color: "text-[#f5a623]" };
    if (kappa >= 0.21) return { label: "Fair", color: "text-[#f5a623]" };
    return { label: "Slight", color: "text-[#e5484d]" };
  };
  const kappaInfo = getKappaInfo(runStats.cohen_kappa);

  return (
    <div className="flex h-full flex-col">
      {/* Stats Header */}
      <div className="grid grid-cols-5 gap-4 p-4 border-b border-border">
        <div className="text-center">
          <div className={`text-2xl font-bold ${accuracyColor}`}>
            {runStats.accuracy.toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground">Accuracy</div>
        </div>
        <div className="text-center">
          <div className={`text-2xl font-bold ${kappaInfo.color}`}>
            {runStats.cohen_kappa.toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground">
            Cohen&apos;s κ ({kappaInfo.label})
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-[#30a46c]">
            {runStats.passed}
          </div>
          <div className="text-xs text-muted-foreground">Correct</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-[#e5484d]">
            {runStats.failed}
          </div>
          <div className="text-xs text-muted-foreground">Incorrect</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-[#f5a623]">
            {runStats.errors}
          </div>
          <div className="text-xs text-muted-foreground">Errors</div>
        </div>
      </div>

      {/* Results Table */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="w-[5%]"></TableHead>
              <TableHead className="w-[8%]">Split</TableHead>
              <TableHead className="w-[30%]">Input</TableHead>
              <TableHead className="w-[10%]">Expected</TableHead>
              <TableHead className="w-[10%]">Actual</TableHead>
              <TableHead className="w-[37%]">Judge Reasoning</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runStats.results.map((result) => {
              const testCase = testCaseLookup[result.test_case_id];
              const isCorrect = result.correct;
              const isError = result.actual_verdict === "ERROR";

              return (
                <TableRow
                  key={result.test_case_id}
                  className={`border-border ${
                    isError
                      ? "bg-[#f5a623]/5"
                      : !isCorrect
                      ? "bg-[#e5484d]/5"
                      : ""
                  }`}
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
                  <TableCell>
                    {testCase?.split ? (
                      <Badge
                        variant="outline"
                        className={
                          testCase.split === "train"
                            ? "border-blue-500 text-blue-500"
                            : "border-purple-500 text-purple-500"
                        }
                      >
                        {testCase.split}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground text-xs">-</span>
                    )}
                  </TableCell>
                  <TableCell className="font-mono text-sm max-w-0">
                    <div
                      className="truncate"
                      title={testCase?.input_text || "Unknown"}
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
                  <TableCell className="text-muted-foreground text-sm max-w-0">
                    <div className="truncate" title={result.reasoning}>
                      {result.reasoning}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
