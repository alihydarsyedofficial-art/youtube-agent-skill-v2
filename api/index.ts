import type { IncomingMessage, ServerResponse } from "http";
import { spawn } from "child_process";
import * as path from "path";
import * as fs from "fs";

export type SkillTool = "hookscore" | "retention" | "deadair" | "chapters" | "title" | "swipe";

export interface AgentToolRequest {
  tool: SkillTool;
  payload: Record<string, any>;
}

export interface AgentToolResponse {
  status: "success" | "error";
  tool?: SkillTool;
  runtime_engine?: string;
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
 * Validates request payloads for each specific YouTube automation tool.
 */
function validatePayload(tool: SkillTool, payload: Record<string, any>): string | null {
  if (!payload || typeof payload !== "object") {
    return "Request 'payload' must be a valid JSON object.";
  }
  switch (tool) {
    case "title":
      if (Array.isArray(payload.candidates) && payload.candidates.length > 0) return null;
      if (typeof payload.title === "string" && payload.title.trim().length > 0) return null;
      return "Tool 'title' requires either 'payload.title' (string) or 'payload.candidates' (array).";
    case "hookscore":
    case "retention":
    case "deadair":
    case "chapters":
    case "swipe":
      if (typeof payload.text !== "string" || payload.text.trim().length === 0) {
        return `Tool '${tool}' requires a non-empty 'payload.text' string.`;
      }
      return null;
    default:
      return `Unsupported tool identifier: '${String(tool)}`;
  }
}

/**
 * Executes Python scripts securely via stdin JSON piping across multi-platform binaries.
 */
function runPythonSubprocess(scriptPath: string, payload: Record<string, any>): Promise<any> {
  const binaries = process.platform === "win32" ? ["python", "py", "python3"] : ["python3", "python"];

  const tryBinary = (index: number): Promise<any> => {
    if (index >= binaries.length) {
      return Promise.reject(new Error("No compatible Python runtime binary found in environment PATH."));
    }
    const bin = binaries[index];
    return new Promise((resolve, reject) => {
      const child = spawn(bin, [scriptPath, "--json-stdin"], {
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 14000,
      });

      let stdout = "";
      let stderr = "";

      child.stdout.on("data", (chunk) => {
        stdout += chunk.toString();
      });
      child.stderr.on("data", (chunk) => {
        stderr += chunk.toString();
      });

      child.on("error", () => {
        tryBinary(index + 1).then(resolve).catch(reject);
      });

      child.on("close", (code) => {
        if (code !== 0) {
          return reject(new Error(stderr.trim() || `Python utility exited with error code ${code}`));
        }
        try {
          resolve(JSON.parse(stdout.trim()));
        } catch (parseErr) {
          reject(new Error(`Failed to parse JSON response from Python script: ${stdout.trim()}`));
        }
      });

      child.stdin.write(JSON.stringify(payload));
      child.stdin.end();
    });
  };

  return tryBinary(0);
}

/**
 * Core execution dispatcher for agent tool requests.
 */
export async function executeSkillTool(req: AgentToolRequest): Promise<AgentToolResponse> {
  const startTime = Date.now();
  const tool = req?.tool;
  const relativeScriptPath = TOOL_MAP[tool];

  if (!relativeScriptPath) {
    return {
      status: "error",
      execution_ms: Date.now() - startTime,
      error: `Unknown tool '${tool}'. Valid tools: ${Object.keys(TOOL_MAP).join(", ")}`,
    };
  }

  const validationError = validatePayload(tool, req.payload);
  if (validationError) {
    return {
      status: "error",
      tool,
      execution_ms: Date.now() - startTime,
      error: validationError,
    };
  }

  const scriptFullPath = path.resolve(process.cwd(), relativeScriptPath);
  if (!fs.existsSync(scriptFullPath)) {
    return {
      status: "error",
      tool,
      execution_ms: Date.now() - startTime,
      error: `Executable script missing on server filesystem: ${scriptFullPath}`,
    };
  }

  try {
    const resultData = await runPythonSubprocess(scriptFullPath, req.payload);
    return {
      status: "success",
      tool,
      runtime_engine: "python-cli-subprocess",
      execution_ms: Date.now() - startTime,
      data: resultData,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      status: "error",
      tool,
      execution_ms: Date.now() - startTime,
      error: message,
    };
  }
}

/**
 * Vercel Serverless / Node.js HTTP Handler
 */
export default async function handler(
  req: IncomingMessage & { body?: any },
  res: ServerResponse
): Promise<void> {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  const sendJson = (statusCode: number, data: unknown) => {
    res.statusCode = statusCode;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.end(JSON.stringify(data, null, 2));
  };

  if (req.method === "OPTIONS") {
    sendJson(200, { ok: true });
    return;
  }

  const requestUrl = req.url || "/";

  if (req.method === "GET" && (requestUrl.includes("/health") || requestUrl === "/api" || requestUrl === "/api/")) {
    sendJson(200, {
      status: "healthy",
      service: "youtube-agent-skill-suite",
      version: "2.1.0",
      available_tools: Object.keys(TOOL_MAP),
    });
    return;
  }

  if (req.method === "GET" && requestUrl.includes("/skills")) {
    const manifestPath = path.resolve(process.cwd(), ".claude-plugin/plugin.json");
    const manifest = fs.existsSync(manifestPath)
      ? JSON.parse(fs.readFileSync(manifestPath, "utf-8"))
      : { skills: Object.keys(TOOL_MAP) };
    sendJson(200, { status: "success", manifest });
    return;
  }

  if (req.method !== "POST") {
    sendJson(405, {
      status: "error",
      error: "Method Not Allowed. Use GET /api/health for status or POST /api/execute for skill invocation.",
    });
    return;
  }

  try {
    let payloadBody = req.body;
    if (!payloadBody || typeof payloadBody !== "object") {
      let rawData = "";
      for await (const chunk of req) {
        rawData += chunk.toString();
      }
      payloadBody = rawData.trim() ? JSON.parse(rawData) : {};
    }

    const responseResult = await executeSkillTool(payloadBody as AgentToolRequest);
    sendJson(responseResult.status === "success" ? 200 : 400, responseResult);
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    sendJson(400, {
      status: "error",
      execution_ms: 0,
      error: `Failed to parse or process request body: ${errorMsg}`,
    });
  }
}