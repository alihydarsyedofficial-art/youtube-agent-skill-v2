import type { IncomingMessage, ServerResponse } from "http";
import { spawn } from "child_process";
import * as path from "path";
import * as fs from "fs";

export type SkillTool = "hookscore" | "retention" | "deadair" | "chapters" | "title" | "swipe";

export interface AgentToolRequest {
  tool: SkillTool;
  payload: Record<string, any>;
}

const TOOL_MAP: Record<SkillTool, string> = {
  hookscore: "skills/yt-script/hookscore.py",
  retention: "skills/yt-retention/retention.py",
  deadair: "skills/yt-edit/deadair.py",
  chapters: "skills/yt-chapters/chapters.py",
  title: "skills/yt-package/title.py",
  swipe: "skills/yt-viral/swipe.py",
};

function validatePayload(tool: SkillTool, payload: Record<string, any>): string | null {
  if (!payload || typeof payload !== "object") return "Request 'payload' must be a JSON object.";
  if (tool === "title") {
    if (Array.isArray(payload.candidates) && payload.candidates.length > 0) return null;
    if (typeof payload.title === "string" && payload.title.trim()) return null;
    return "Tool 'title' requires 'payload.title' or 'payload.candidates'.";
  }
  if (typeof payload.text !== "string" || !payload.text.trim()) {
    return `Tool '${tool}' requires a non-empty 'payload.text' string.`;
  }
  return null;
}

function runPythonSubprocess(scriptPath: string, payload: Record<string, any>): Promise<any> {
  const binaries = process.platform === "win32" ? ["python", "py", "python3"] : ["python3", "python"];
  const tryBinary = (idx: number): Promise<any> => {
    if (idx >= binaries.length) return Promise.reject(new Error("No Python binary found."));
    return new Promise((resolve, reject) => {
      const child = spawn(binaries[idx], [scriptPath, "--json-stdin"], { stdio: ["pipe", "pipe", "pipe"], timeout: 12000 });
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (c) => (stdout += c.toString()));
      child.stderr.on("data", (c) => (stderr += c.toString()));
      child.on("error", () => tryBinary(idx + 1).then(resolve).catch(reject));
      child.on("close", (code) => {
        if (code !== 0) return reject(new Error(stderr.trim() || `Exited with ${code}`));
        try { resolve(JSON.parse(stdout.trim())); } catch { reject(new Error("Invalid JSON output")); }
      });
      child.stdin.write(JSON.stringify(payload));
      child.stdin.end();
    });
  };
  return tryBinary(0);
}

export async function executeSkillTool(req: AgentToolRequest) {
  const startTime = Date.now();
  const tool = req?.tool;
  const relPath = TOOL_MAP[tool];
  if (!relPath) {
    return { status: "error", execution_ms: Date.now() - startTime, error: `Valid tools: ${Object.keys(TOOL_MAP).join(", ")}` };
  }
  const err = validatePayload(tool, req.payload);
  if (err) return { status: "error", tool, execution_ms: Date.now() - startTime, error: err };

  const fullPath = path.resolve(process.cwd(), relPath);
  try {
    const data = await runPythonSubprocess(fullPath, req.payload);
    return { status: "success", tool, runtime_engine: "python-cli", execution_ms: Date.now() - startTime, data };
  } catch (e: any) {
    return { status: "error", tool, execution_ms: Date.now() - startTime, error: e?.message || String(e) };
  }
}

export default async function handler(req: IncomingMessage & { body?: any }, res: ServerResponse) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  const send = (code: number, obj: unknown) => {
    res.statusCode = code;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.end(JSON.stringify(obj, null, 2));
  };

  if (req.method === "OPTIONS") return send(200, { ok: true });
  const url = req.url || "/";

  if (req.method === "GET" && (url.includes("/health") || url === "/api" || url === "/api/")) {
    return send(200, { status: "healthy", version: "2.1.0", available_tools: Object.keys(TOOL_MAP) });
  }

  if (req.method === "GET" && url.includes("/skills")) {
    const p = path.resolve(process.cwd(), ".claude-plugin/plugin.json");
    const manifest = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf-8")) : {};
    return send(200, { status: "success", manifest });
  }

  if (req.method !== "POST") return send(405, { status: "error", error: "Use GET /api/health or POST /api/execute" });

  let raw = "";
  if (req.body && typeof req.body === "object") {
    const out = await executeSkillTool(req.body);
    return send(out.status === "success" ? 200 : 400, out);
  }
  req.on("data", (c) => (raw += c.toString()));
  req.on("end", async () => {
    try {
      const parsed = JSON.parse(raw || "{}");
      const out = await executeSkillTool(parsed);
      send(out.status === "success" ? 200 : 400, out);
    } catch (e: any) {
      send(400, { status: "error", error: e?.message || "Invalid JSON body" });
    }
  });
}
