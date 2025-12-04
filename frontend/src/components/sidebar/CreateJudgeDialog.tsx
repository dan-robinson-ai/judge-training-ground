"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface CreateJudgeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (name: string) => void;
  existingCount: number;
}

export function CreateJudgeDialog({
  open,
  onOpenChange,
  onSubmit,
  existingCount,
}: CreateJudgeDialogProps) {
  const [name, setName] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const judgeName = name.trim() || `Judge ${existingCount + 1}`;
    onSubmit(judgeName);
    setName("");
    onOpenChange(false);
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setName("");
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create New Judge</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="judge-name">Judge Name</Label>
              <Input
                id="judge-name"
                placeholder={`Judge ${existingCount + 1}`}
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                Leave empty for auto-generated name
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit">Create Judge</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
