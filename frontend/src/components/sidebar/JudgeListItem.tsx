"use client";

import { useState, useRef, useEffect } from "react";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { JudgeListItem as JudgeListItemType } from "@/lib/types";

interface JudgeListItemProps {
  judge: JudgeListItemType;
  isActive: boolean;
  collapsed: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (newName: string) => void;
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function getAccuracyColor(accuracy: number | null): string {
  if (accuracy === null) return "bg-muted text-muted-foreground";
  if (accuracy >= 90) return "bg-green-500/20 text-green-400";
  if (accuracy >= 70) return "bg-yellow-500/20 text-yellow-400";
  return "bg-red-500/20 text-red-400";
}

export function JudgeListItemComponent({
  judge,
  isActive,
  collapsed,
  onSelect,
  onDelete,
  onRename,
}: JudgeListItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(judge.name);
  const [isHovered, setIsHovered] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleDoubleClick = () => {
    if (!collapsed) {
      setEditName(judge.name);
      setIsEditing(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      if (editName.trim() && editName !== judge.name) {
        onRename(editName.trim());
      }
      setIsEditing(false);
    } else if (e.key === "Escape") {
      setEditName(judge.name);
      setIsEditing(false);
    }
  };

  const handleBlur = () => {
    if (editName.trim() && editName !== judge.name) {
      onRename(editName.trim());
    }
    setIsEditing(false);
  };

  // Collapsed view - just show avatar
  if (collapsed) {
    return (
      <button
        onClick={onSelect}
        className={`
          w-10 h-10 rounded-lg flex items-center justify-center text-sm font-medium
          transition-colors
          ${isActive
            ? "bg-primary text-primary-foreground ring-2 ring-primary/50"
            : "bg-secondary/50 text-foreground hover:bg-secondary"
          }
        `}
        title={judge.name}
      >
        {judge.name.charAt(0).toUpperCase()}
      </button>
    );
  }

  // Expanded view
  return (
    <div
      className={`
        group relative px-3 py-2 rounded-lg cursor-pointer transition-colors
        ${isActive ? "bg-secondary" : "hover:bg-secondary/50"}
      `}
      onClick={onSelect}
      onDoubleClick={handleDoubleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <input
              ref={inputRef}
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleBlur}
              onClick={(e) => e.stopPropagation()}
              className="w-full bg-background border border-border rounded px-2 py-0.5 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-primary"
            />
          ) : (
            <div className="text-sm font-medium truncate">{judge.name}</div>
          )}
          <div className="text-xs text-muted-foreground mt-0.5">
            {formatTimeAgo(judge.updatedAt)}
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {judge.accuracy !== null && (
            <Badge
              variant="secondary"
              className={`text-xs px-1.5 py-0 ${getAccuracyColor(judge.accuracy)}`}
            >
              {Math.round(judge.accuracy)}%
            </Badge>
          )}
          {isHovered && !isEditing && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 rounded hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
      {judge.testCaseCount > 0 && (
        <div className="text-xs text-muted-foreground mt-1">
          {judge.testCaseCount} test case{judge.testCaseCount !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
