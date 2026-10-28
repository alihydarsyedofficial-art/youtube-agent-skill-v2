import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as fs from "fs";

const execFileAsync = promisify(execFile);

export type SkillTool =
  | "hookscore"
  | "retention"
  | "deadair"
  | "chapters"
  | "title"
  | "swipe";

export interface AgentToolRequest {
  tool: SkillTool;
  payload: Record<string, unknown>;
}

export interface AgentToolResponse {
  status: "success" | "error";
  tool: SkillTool;
  execution_ms: number;
  data?: unknown;
  error?: string;
}

const TOOL_MAP: Record<SkillTool, string> = {
  hookscore: "skills/yt-script/hookscore.py",
  retention: "skills/yt-retention/retention.py",
  deadair: "skills/yt-edit/deadair.py",
  chapters: "skills/yt-chapters/chapters.py",
  title: "skills/yt-package/title.py",
  swipe: "skills/yt-viral/swipe.py",
};

/**
 * Executes a Python skill script deterministically via stdin JSON piping.
 * Zero temporary file overhead, serverless-safe, and injection-proof.
 */
export async function executeSkillTool(req: AgentToolRequest): Promise<AgentToolResponse> {
  const startTime = Date.now();
  const relativeScriptPath = TOOL_MAP[req.tool];

  if (!relativeScriptPath) {
    return {
      status: "error",
      tool: req.tool,
      execution_ms: Date.now() - startTime,
      error: `Unknown tool '${req.tool}'. Valid tools: ${Object.keys(TOOL_MAP).join(", ")}`,
    };
  }

  const scriptFullPath = path.resolve(process.cwd(), relativeScriptPath);
  if (!fs.existsSync(scriptFullPath)) {
    return {
      status: "error",
      tool: req.tool,
      execution_ms: Date.now() - startTime,
      error: `Script binary not found at path: ${scriptFullPath}`,
    };
  }

  try {
    const inputJson = JSON.stringify(req.payload);
    const promise = execFileAsync("python3", [scriptFullPath, "--json-stdin"], {
      timeout: 15000,
      maxBuffer: 1024 * 1024 * 5,
    });

    const child = promise.child;
    if (child.stdin) {
      child.stdin.write(inputJson);
      child.stdin.end();
    }

    const { stdout } = await promise;
    const parsedData = JSON.parse(stdout.trim());

    return {
      status: "success",
      tool: req.tool,
      execution_ms: Date.now() - startTime,
      data: parsedData,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      status: "error",
      tool: req.tool,
      execution_ms: Date.now() - startTime,
      error: message,
    };
  }
}

/**
 * Serverless HTTP Handler (Vercel / AWS Lambda / Cloudflare Node compat)
 */
export default async function handler(req: any, res: any) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method Not Allowed. Use POST." });
    return;
  }
  const result = await executeSkillTool(req.body as AgentToolRequest);
  res.status(result.status === "success" ? 200 : 400).json(result);
}