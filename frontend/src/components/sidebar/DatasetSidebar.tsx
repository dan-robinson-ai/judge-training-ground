"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DatasetListItemComponent } from "./DatasetListItem";
import { CreateDatasetDialog } from "./CreateDatasetDialog";
import { useTrainingStore } from "@/lib/store";

export function DatasetSidebar() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const {
    sidebarCollapsed,
    toggleSidebar,
    datasets,
    activeDatasetId,
    selectDataset,
    createDataset,
    deleteDataset,
    renameDataset,
  } = useTrainingStore();

  const handleCreateDataset = async (name: string) => {
    await createDataset(name);
  };

  const handleDeleteDataset = async (id: string) => {
    if (window.confirm("Are you sure you want to delete this dataset?")) {
      await deleteDataset(id);
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
                {datasets.length}
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
          {datasets.length === 0 ? (
            !sidebarCollapsed && (
              <div className="text-center text-sm text-muted-foreground py-8 px-4">
                No judges yet.
                <br />
                Create one to get started.
              </div>
            )
          ) : (
            <div className={`space-y-1 ${sidebarCollapsed ? "flex flex-col items-center" : ""}`}>
              {datasets.map((dataset) => (
                <DatasetListItemComponent
                  key={dataset.id}
                  dataset={dataset}
                  isActive={dataset.id === activeDatasetId}
                  collapsed={sidebarCollapsed}
                  onSelect={() => selectDataset(dataset.id)}
                  onDelete={() => handleDeleteDataset(dataset.id)}
                  onRename={(newName) => renameDataset(dataset.id, newName)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <CreateDatasetDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSubmit={handleCreateDataset}
        existingCount={datasets.length}
      />
    </>
  );
}
