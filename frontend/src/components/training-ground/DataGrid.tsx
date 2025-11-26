"use client";

import { useState } from "react";
import { useTrainingStore } from "@/lib/store";
import { TestCase } from "@/lib/types";
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
  DialogFooter,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Trash2, Edit2, CheckCircle, Plus } from "lucide-react";

interface EditDialogProps {
  testCase: TestCase | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (testCase: TestCase) => void;
  isNew?: boolean;
}

function EditDialog({
  testCase,
  open,
  onOpenChange,
  onSave,
  isNew = false,
}: EditDialogProps) {
  const [inputText, setInputText] = useState("");
  const [expectedVerdict, setExpectedVerdict] = useState<"PASS" | "FAIL">("PASS");
  const [reasoning, setReasoning] = useState("");

  // Reset form when dialog opens with new data
  const handleOpenChange = (newOpen: boolean) => {
    if (newOpen) {
      setInputText(testCase?.input_text || "");
      setExpectedVerdict(testCase?.expected_verdict || "PASS");
      setReasoning(testCase?.reasoning || "");
    }
    onOpenChange(newOpen);
  };

  const handleSave = () => {
    onSave({
      id: testCase?.id || crypto.randomUUID(),
      input_text: inputText,
      expected_verdict: expectedVerdict,
      reasoning,
      verified: true,
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isNew ? "Add Test Case" : "Edit Test Case"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="input">Input Text</Label>
            <Textarea
              id="input"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="The text to evaluate..."
              className="min-h-[100px]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="verdict">Expected Verdict</Label>
            <Select
              value={expectedVerdict}
              onValueChange={(v) => setExpectedVerdict(v as "PASS" | "FAIL")}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PASS">PASS</SelectItem>
                <SelectItem value="FAIL">FAIL</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="reasoning">Reasoning</Label>
            <Textarea
              id="reasoning"
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              placeholder="Why should this pass/fail..."
              className="min-h-[80px]"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!inputText.trim()}>
            {isNew ? "Add" : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function DataGrid() {
  const { testCases, updateTestCase, deleteTestCase, addTestCase, isGenerating } =
    useTrainingStore();
  const [editingTestCase, setEditingTestCase] = useState<TestCase | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

  const handleEdit = (testCase: TestCase) => {
    setEditingTestCase(testCase);
    setIsEditDialogOpen(true);
  };

  const handleSaveEdit = (updated: TestCase) => {
    updateTestCase(updated.id, updated);
  };

  const handleAddNew = (newCase: TestCase) => {
    addTestCase(newCase);
  };

  const toggleVerdict = (testCase: TestCase) => {
    updateTestCase(testCase.id, {
      expected_verdict: testCase.expected_verdict === "PASS" ? "FAIL" : "PASS",
      verified: true,
    });
  };

  if (testCases.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center p-8">
        <div className="rounded-full bg-secondary p-4">
          <Plus className="h-8 w-8 text-muted-foreground" />
        </div>
        <div>
          <h3 className="font-medium text-foreground">No test cases yet</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {isGenerating
              ? "Generating test cases..."
              : "Enter an intent and click Generate to create test cases"}
          </p>
        </div>
        <Button variant="secondary" onClick={() => setIsAddDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Manually
        </Button>
        <EditDialog
          testCase={null}
          open={isAddDialogOpen}
          onOpenChange={setIsAddDialogOpen}
          onSave={handleAddNew}
          isNew
        />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="text-sm text-muted-foreground">
          {testCases.length} test case{testCases.length !== 1 ? "s" : ""}
          <span className="mx-2">·</span>
          <span className="text-[#30a46c]">
            {testCases.filter((tc) => tc.expected_verdict === "PASS").length} pass
          </span>
          <span className="mx-2">·</span>
          <span className="text-[#e5484d]">
            {testCases.filter((tc) => tc.expected_verdict === "FAIL").length} fail
          </span>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => setIsAddDialogOpen(true)}
        >
          <Plus className="mr-2 h-4 w-4" />
          Add
        </Button>
      </div>
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="w-[50%]">Input</TableHead>
              <TableHead className="w-[15%]">Expected</TableHead>
              <TableHead className="w-[25%]">Reasoning</TableHead>
              <TableHead className="w-[10%] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {testCases.map((testCase) => (
              <TableRow
                key={testCase.id}
                className="cursor-pointer hover:bg-secondary/50 border-border"
                onClick={() => handleEdit(testCase)}
              >
                <TableCell className="font-mono text-sm max-w-0">
                  <div className="truncate" title={testCase.input_text}>
                    {testCase.input_text}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={`cursor-pointer transition-colors ${
                      testCase.expected_verdict === "PASS"
                        ? "border-[#30a46c] text-[#30a46c] hover:bg-[#30a46c]/10"
                        : "border-[#e5484d] text-[#e5484d] hover:bg-[#e5484d]/10"
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleVerdict(testCase);
                    }}
                  >
                    {testCase.expected_verdict}
                  </Badge>
                  {testCase.verified && (
                    <CheckCircle className="inline-block ml-2 h-3 w-3 text-[#30a46c]" />
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground text-sm max-w-0">
                  <div className="truncate" title={testCase.reasoning}>
                    {testCase.reasoning}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(testCase);
                      }}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteTestCase(testCase.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <EditDialog
        testCase={editingTestCase}
        open={isEditDialogOpen}
        onOpenChange={setIsEditDialogOpen}
        onSave={handleSaveEdit}
      />
      <EditDialog
        testCase={null}
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
        onSave={handleAddNew}
        isNew
      />
    </div>
  );
}
