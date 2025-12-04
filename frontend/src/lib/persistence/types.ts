import { Judge, JudgeListItem } from "../types";

export interface JudgeStorageProvider {
  getAllJudges(): Promise<JudgeListItem[]>;
  getJudge(id: string): Promise<Judge | null>;
  saveJudge(judge: Judge): Promise<void>;
  deleteJudge(id: string): Promise<void>;
}
