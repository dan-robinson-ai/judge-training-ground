"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { JudgeListItemComponent } from "./JudgeListItem";
import { CreateJudgeDialog } from "./CreateJudgeDialog";
import { useTrainingStore } from "@/lib/store";

export function JudgeSidebar() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const {
    sidebarCollapsed,
    toggleSidebar,
    judges,
    activeJudgeId,
    selectJudge,
    createJudge,
    deleteJudge,
    renameJudge,
  } = useTrainingStore();

  const handleCreateJudge = async (name: string) => {
    await createJudge(name);
  };

  const handleDeleteJudge = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this judge?")) {
      await deleteJudge(id);
    }
  };

  return (
    <>
      <div
        className={`
          flex flex-col border-r border-border bg-background transition-all duration-200
          ${sidebarCollapsed ? "w-16" : "w-72"}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-12 px-3 border-b border-border">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Judges</span>
              <Badge variant="secondary" className="text-xs">
                {judges.length}
              </Badge>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className={`h-8 w-8 ${sidebarCollapsed ? "mx-auto" : ""}`}
            onClick={toggleSidebar}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* New Judge Button */}
        <div className="p-2 border-b border-border">
          {sidebarCollapsed ? (
            <Button
              variant="ghost"
              size="icon"
              className="w-10 h-10 mx-auto"
              onClick={() => setIsCreateDialogOpen(true)}
              title="New Judge"
            >
              <Plus className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={() => setIsCreateDialogOpen(true)}
            >
              <Plus className="h-4 w-4" />
              New Judge
            </Button>
          )}
        </div>

        {/* Judge List */}
        <div className="flex-1 overflow-y-auto p-2">
          {judges.length === 0 ? (
            !sidebarCollapsed && (
              <div className="text-center text-sm text-muted-foreground py-8 px-4">
                No judges yet.
                <br />
                Create one to get started.
              </div>
            )
          ) : (
            <div className={`space-y-1 ${sidebarCollapsed ? "flex flex-col items-center" : ""}`}>
              {judges.map((judge) => (
                <JudgeListItemComponent
                  key={judge.id}
                  judge={judge}
                  isActive={judge.id === activeJudgeId}
                  collapsed={sidebarCollapsed}
                  onSelect={() => selectJudge(judge.id)}
                  onDelete={() => handleDeleteJudge(judge.id)}
                  onRename={(newName) => renameJudge(judge.id, newName)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <CreateJudgeDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSubmit={handleCreateJudge}
        existingCount={judges.length}
      />
    </>
  );
}
