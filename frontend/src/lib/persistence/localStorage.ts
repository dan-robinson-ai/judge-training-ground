import { Judge, JudgeListItem } from "../types";
import { JudgeStorageProvider } from "./types";

const INDEX_KEY = "judge-training-index";
const JUDGE_KEY_PREFIX = "judge-training-judges-";

export class LocalStorageProvider implements JudgeStorageProvider {
  async getAllJudges(): Promise<JudgeListItem[]> {
    if (typeof window === "undefined") return [];
    const index = localStorage.getItem(INDEX_KEY);
    return index ? JSON.parse(index) : [];
  }

  async getJudge(id: string): Promise<Judge | null> {
    if (typeof window === "undefined") return null;
    const data = localStorage.getItem(`${JUDGE_KEY_PREFIX}${id}`);
    return data ? JSON.parse(data) : null;
  }

  async saveJudge(judge: Judge): Promise<void> {
    if (typeof window === "undefined") return;

    // Update timestamp
    const updatedJudge = {
      ...judge,
      updatedAt: new Date().toISOString(),
    };

    // Save full judge data
    localStorage.setItem(
      `${JUDGE_KEY_PREFIX}${judge.id}`,
      JSON.stringify(updatedJudge)
    );

    // Update index
    const index = await this.getAllJudges();
    const listItem: JudgeListItem = {
      id: judge.id,
      name: judge.name,
      createdAt: judge.createdAt,
      updatedAt: updatedJudge.updatedAt,
      testCaseCount: judge.testCases.length,
      accuracy: judge.runStats?.accuracy ?? null,
    };

    const existingIdx = index.findIndex((j) => j.id === judge.id);
    if (existingIdx >= 0) {
      index[existingIdx] = listItem;
    } else {
      index.push(listItem);
    }
    localStorage.setItem(INDEX_KEY, JSON.stringify(index));
  }

  async deleteJudge(id: string): Promise<void> {
    if (typeof window === "undefined") return;
    localStorage.removeItem(`${JUDGE_KEY_PREFIX}${id}`);
    const index = await this.getAllJudges();
    localStorage.setItem(
      INDEX_KEY,
      JSON.stringify(index.filter((j) => j.id !== id))
    );
  }
}
