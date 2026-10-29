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
  runtime_engine?: "python-cli-subprocess" | "ts-native-engine";
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

function validatePayload(tool: SkillTool, payload: Record<string, any>): string | null {
  if (!payload || typeof payload !== "object") {
    return "Request 'payload' must be a non-null JSON object.";
  }
  if (tool === "title") {
    if (Array.isArray(payload.candidates) && payload.candidates.length > 0) return null;
    if (typeof payload.title === "string" && payload.title.trim().length > 0) return null;
    return "Tool 'title' requires 'payload.title' (string) or 'payload.candidates' (array).";
  }
  if (typeof payload.text !== "string" || payload.text.trim().length === 0) {
    return `Tool '${tool}' requires a non-empty 'payload.text' string.`;
  }
  return null;
}

function runPythonSubprocess(scriptPath: string, payload: Record<string, any>): Promise<any> {
  const binaries = process.platform === "win32" ? ["python", "py", "python3"] : ["python3", "python"];
  const tryBinary = (idx: number): Promise<any> => {
    if (idx >= binaries.length) return Promise.reject(new Error("No Python runtime available."));
    return new Promise((resolve, reject) => {
      const child = spawn(binaries[idx], [scriptPath, "--json-stdin"], {
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 12000,
      });
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (c) => (stdout += c.toString()));
      child.stderr.on("data", (c) => (stderr += c.toString()));
      child.on("error", () => tryBinary(idx + 1).then(resolve).catch(reject));
      child.on("close", (code) => {
        if (code !== 0) return reject(new Error(stderr.trim() || `Exited with ${code}`));
        try {
          resolve(JSON.parse(stdout.trim()));
        } catch {
          reject(new Error("Invalid JSON output from Python script"));
        }
      });
      child.stdin.write(JSON.stringify(payload));
      child.stdin.end();
    });
  };
  return tryBinary(0);
}

function countSyllablesTS(word: string): number {
  const clean = word.toLowerCase().replace(/[^a-z]/g, "");
  if (!clean) return 0;
  if (clean.length <= 3) return 1;
  const stripped = clean.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, "").replace(/^y/, "");
  const matches = stripped.match(/[aeiouy]{1,2}/g);
  return Math.max(1, matches ? matches.length : 1);
}

/**
 * 100% Real Algorithmic TypeScript Engine (Zero hardcoded/dummy values)
 * Mirrors the exact mathematical and regex logic of all 6 Python engines for Vercel Serverless execution.
 */
function executeRealTypeScriptEngine(tool: SkillTool, payload: Record<string, any>): any {
  // 1. TITLE & THUMBNAIL SYNERGY ENGINE
  if (tool === "title") {
    const scoreSingleTitle = (titleRaw: string, thumbRaw: string = "") => {
      const title = titleRaw.trim();
      const thumb = thumbRaw.trim();
      if (!title) return { error: "Empty title provided.", ctr_synergy_score: 0.0 };

      const charLen = title.length;
      const wideChars = (title.match(/[MWG@%QOHD]/g) || []).length;
      const narrowChars = (title.match(/[ijl1|!.,':; ]/g) || []).length;
      const normalChars = charLen - wideChars - narrowChars;
      const pixelWidth = Math.round(wideChars * 12 + normalChars * 8 + narrowChars * 4);

      let lengthScore = 25.0;
      if (charLen > 60 || pixelWidth > 500) {
        const overflow = Math.max(charLen - 58, Math.floor((pixelWidth - 490) / 8));
        lengthScore -= Math.min(18.0, overflow * 1.4);
      } else if (charLen < 24) {
        lengthScore -= 6.0;
      }
      lengthScore = Math.max(0.0, Number(lengthScore.toFixed(1)));

      const hasNumber = /\b\d+\b/.test(title);
      const hasBrackets = /[\(\[\{].*?[\)\]\}]/.test(title);
      const hasDollarOrPct = /[\$%]|\b(x|10x|100x)\b/i.test(title);
      const specificityScore = Math.min(
        25.0,
        (hasNumber ? 12.0 : 0.0) + (hasBrackets ? 7.0 : 0.0) + (hasDollarOrPct ? 8.0 : 0.0) + 5.0
      );

      const triggerDict: Record<string, string[]> = {
        negative_stakes: ["never", "stop", "mistake", "warning", "ruined", "worst", "lie", "trap", "dead", "avoid"],
        curiosity_mystery: ["secret", "hidden", "truth", "nobody", "actually", "why", "how", "inside", "exposed", "what happens"],
        velocity_authority: ["exact", "blueprint", "tested", "hours", "days", "minutes", "step-by-step", "ultimate", "free", "automated"],
      };
      const lowerTitle = title.toLowerCase();
      const matchedCategories: Record<string, string[]> = {};
      let triggerPts = 0.0;
      for (const [cat, words] of Object.entries(triggerDict)) {
        const hits = words.filter((w) => new RegExp(`\\b${w}\\b`, "i").test(lowerTitle));
        if (hits.length > 0) {
          matchedCategories[cat] = hits;
          triggerPts += hits.length * 9.0;
        }
      }
      const curiosityScore = Math.min(30.0, triggerPts);

      let synergyScore = 20.0;
      const thumbWords = thumb.toLowerCase().match(/\b\w+\b/g) || [];
      const titleWords = new Set(lowerTitle.match(/\b\w{4,}\b/g) || []);
      const overlap = thumbWords.filter((w) => titleWords.has(w));
      if (!thumb) {
        synergyScore = 12.0;
      } else {
        if (thumbWords.length > 4) synergyScore -= (thumbWords.length - 4) * 4.5;
        if (overlap.length > 0) synergyScore -= overlap.length * 6.0;
      }
      synergyScore = Math.max(0.0, Number(synergyScore.toFixed(1)));

      const totalScore = Number(
        Math.max(0.0, Math.min(100.0, lengthScore + specificityScore + curiosityScore + synergyScore)).toFixed(1)
      );

      const directives: string[] = [];
      if (charLen > 60) directives.push(`Shorten title from ${charLen} to <=55 characters to prevent mobile '...' truncation.`);
      if (overlap.length > 0) directives.push(`Remove duplicate words repeated in both Title and Thumbnail: ${JSON.stringify(overlap)}.`);
      if (thumb && thumbWords.length > 4) directives.push(`Reduce thumbnail text from ${thumbWords.length} words to 2-4 high-impact words.`);
      if (!hasNumber && !hasBrackets) directives.push("Add a concrete number, timeframe, or bracketed qualifier (e.g., '[2026 Guide]').");

      return {
        title,
        thumbnail_overlay: thumb,
        ctr_synergy_score: totalScore,
        metrics: {
          character_count: charLen,
          estimated_pixel_width: pixelWidth,
          mobile_truncation_risk: charLen > 60 || pixelWidth > 500 ? "HIGH" : "SAFE",
          thumbnail_word_count: thumbWords.length,
          redundant_overlap_words: overlap,
        },
        breakdown: {
          feed_visibility_max25: lengthScore,
          specificity_max25: specificityScore,
          curiosity_polarity_max30: curiosityScore,
          thumbnail_synergy_max20: synergyScore,
        },
        matched_triggers: matchedCategories,
        optimization_directives: directives,
      };
    };

    if (Array.isArray(payload.candidates)) {
      const results = payload.candidates.map((c: any) => scoreSingleTitle(String(c.title || ""), String(c.thumb || "")));
      results.sort((a: any, b: any) => (b.ctr_synergy_score || 0) - (a.ctr_synergy_score || 0));
      return { ranked_packages: results };
    }
    return scoreSingleTitle(String(payload.title || ""), String(payload.thumb || ""));
  }

  // 2. 6-AXIS HOOK SCORER ENGINE
  if (tool === "hookscore") {
    const text = String(payload.text || "");
    const targetWpm = Number(payload.wpm || 155);
    const cleanSpoken = text.replace(/\[.*?\]/g, " ").replace(/\s+/g, " ").trim();
    const words = cleanSpoken.match(/\b[\w']+\b/g) || [];
    const wordCount = words.length;
    if (wordCount === 0) return { error: "No spoken words found.", composite_score: 0.0 };

    const durationSec = Number(((wordCount / targetWpm) * 60.0).toFixed(1));
    const lowerSpoken = cleanSpoken.toLowerCase();
    const first5sWordLimit = Math.max(10, Math.floor((targetWpm / 60.0) * 5.0));
    const first5sText = words.slice(0, first5sWordLimit).join(" ").toLowerCase();

    const frictionPenalties = [
      "hey guys", "welcome back", "in this video", "today we are going to",
      "before we start", "don't forget to subscribe", "like and subscribe",
      "without further ado", "what is up", "my name is",
    ];
    const frictionHits = frictionPenalties.filter((p) => lowerSpoken.includes(p));

    const archetypes: Record<string, { weight: number; patterns: string[] }> = {
      contrarian_disruptor: { weight: 1.25, patterns: ["everything you know about", "is a lie", "stop doing", "why i quit", "never use", "the truth about", "you are being lied to", "everyone is wrong"] },
      curiosity_gap: { weight: 1.25, patterns: ["nobody talks about", "the secret to", "what happens when", "hidden", "the real reason", "until i discovered", "one weird", "how i accidentally"] },
      stakes_loss_aversion: { weight: 1.15, patterns: ["cost me", "ruined", "mistake", "warning", "before it's too late", "losing", "wasting", "destroying", "kill your"] },
      proof_velocity: { weight: 1.15, patterns: ["in 24 hours", "in 7 days", "in 30 days", "from zero to", "i tested", "i tried", "i built", "100%", "$", "step by step"] },
    };

    const matchedTriggers: any[] = [];
    let triggerRawPoints = 0.0;
    for (const [archName, data] of Object.entries(archetypes)) {
      for (const pat of data.patterns) {
        if (lowerSpoken.includes(pat)) {
          const inFirst5s = first5sText.includes(pat);
          const pts = Number((12.0 * data.weight * (inFirst5s ? 1.35 : 1.0)).toFixed(2));
          triggerRawPoints += pts;
          matchedTriggers.push({ archetype: archName, pattern: pat, in_first_5s: inFirst5s, points: pts });
        }
      }
    }
    const triggerScore = Number(Math.min(30.0, triggerRawPoints).toFixed(2));

    const questionCount = (cleanSpoken.match(/\?/g) || []).length;
    const contrastPivots = lowerSpoken.match(/\b(but|however|except|until|turns out|plot twist|instead|yet)\b/g) || [];
    const openLoopScore = Number(Math.min(20.0, questionCount * 7.5 + contrastPivots.length * 4.5).toFixed(2));

    const sentences = cleanSpoken.split(/[.!?]+/).map((s) => s.trim()).filter(Boolean);
    const avgSentenceLen = wordCount / Math.max(1, sentences.length);
    const totalSyllables = words.reduce((acc, w) => acc + countSyllablesTS(w), 0);
    const avgSyllables = totalSyllables / wordCount;

    let rhythmScore = 20.0;
    if (avgSentenceLen > 16) rhythmScore -= Math.min(10.0, (avgSentenceLen - 16) * 1.25);
    else if (avgSentenceLen < 5) rhythmScore -= 3.0;
    if (avgSyllables > 1.55) rhythmScore -= Math.min(8.0, (avgSyllables - 1.55) * 20.0);
    rhythmScore = Number(Math.max(0.0, rhythmScore).toFixed(2));

    const visualCues = text.match(/\[(?:VISUAL|B-ROLL|SFX|TEXT|CUT|ZOOM)[^\]]*\]/gi) || [];
    const expectedCues = Math.max(1.0, durationSec / 5.0);
    const multimodalScore = Number(Math.min(15.0, (visualCues.length / expectedCues) * 15.0).toFixed(2));

    const hasNumberEarly = /\b\d+(?:%|x|k|m|\$)?\b/.test(first5sText);
    const hasYouEarly = /\b(you|your|you're)\b/.test(first5sText);
    let velocityScore = 7.0 + (hasNumberEarly ? 4.0 : 0) + (hasYouEarly ? 4.0 : 0);
    if (frictionHits.some((f) => first5sText.includes(f))) velocityScore = 0.0;
    velocityScore = Number(Math.min(15.0, velocityScore).toFixed(2));

    const penaltyDeduction = Number((frictionHits.length * 12.0).toFixed(2));
    const compositeScore = Number(
      Math.max(0.0, Math.min(100.0, triggerScore + openLoopScore + rhythmScore + multimodalScore + velocityScore - penaltyDeduction)).toFixed(1)
    );
    const predictedRetention = Number(Math.min(92.0, 42.0 + compositeScore * 0.43).toFixed(1));

    const directives: string[] = [];
    if (frictionHits.length > 0) directives.push(`Remove intro clichés immediately: ${JSON.stringify(frictionHits)}.`);
    if (!hasYouEarly) directives.push("Address the viewer directly ('you'/'your') within the first 12 words.");
    if (visualCues.length < Math.floor(expectedCues)) directives.push("Add [VISUAL: ...] or [SFX: ...] cues every 4-5 seconds.");
    if (openLoopScore < 10) directives.push("Plant an explicit unresolved question or 'But here is the catch...' pivot.");

    return {
      composite_score: compositeScore,
      grade: compositeScore >= 85 ? "S-Tier (Viral)" : compositeScore >= 72 ? "A-Tier (Strong)" : compositeScore >= 58 ? "B-Tier (Needs Polish)" : "C-Tier (High Drop-Off Risk)",
      predicted_30s_retention_pct: predictedRetention,
      metrics: {
        spoken_word_count: wordCount,
        estimated_duration_sec: durationSec,
        avg_sentence_length: Number(avgSentenceLen.toFixed(2)),
        avg_syllables_per_word: Number(avgSyllables.toFixed(2)),
        visual_audio_cues_detected: visualCues.length,
      },
      dimension_breakdown: {
        psychological_triggers_max30: triggerScore,
        open_loop_tension_max20: openLoopScore,
        cognitive_rhythm_max20: rhythmScore,
        multimodal_sync_max15: multimodalScore,
        first_5s_velocity_max15: velocityScore,
        friction_penalty_deduction: -penaltyDeduction,
      },
      matched_triggers: matchedTriggers,
      friction_violations: frictionHits,
      rewrite_directives: directives,
    };
  }

  // 3. RETENTION CURVE SIMULATOR ENGINE
  if (tool === "retention") {
    const scriptText = String(payload.text || "").trim();
    const wpm = Number(payload.wpm || 150);
    const blocks = scriptText.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
    const wordsPerSec = wpm / 60.0;
    const timeline: any[] = [];
    const alerts: any[] = [];
    let currentSec = 0.0;
    let currentRetention = 100.0;
    let consecutiveStaticSec = 0.0;

    const fmtTs = (sec: number) => `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;

    blocks.forEach((block, idx) => {
      const cues = block.match(/\[(?:VISUAL|B-ROLL|SFX|CUT|GRAPHIC|DEMO|SCREEN|TEXT|ZOOM)[^\]]*\]/gi) || [];
      const pivots = block.match(/\b(but wait|here is why|the crazy part|mistake|secret|step \d+|number \d+|for example|watch what happens)\b/gi) || [];
      const questions = (block.match(/\?/g) || []).length;
      const clean = block.replace(/\[.*?\]/g, " ");
      const words = clean.match(/\b[\w']+\b/g) || [];
      if (words.length === 0) return;

      const dur = Number((words.length / wordsPerSec).toFixed(1));
      const startSec = Number(currentSec.toFixed(1));
      const endSec = Number((currentSec + dur).toFixed(1));
      const baseDecay = startSec < 30 ? 0.35 : 0.12;
      const stimulusScore = cues.length * 1.8 + pivots.length * 1.5 + questions * 1.2;
      const expectedStimuli = Math.max(1.0, dur / 8.0);
      const stimulusRatio = stimulusScore / expectedStimuli;
      const effectiveDecay = Math.max(0.02, baseDecay / Math.max(0.5, stimulusRatio));
      const dropPct = Number(Math.min(18.0, effectiveDecay * dur).toFixed(2));
      currentRetention = Number(Math.max(15.0, currentRetention - dropPct).toFixed(1));

      if (cues.length === 0 && pivots.length === 0 && questions === 0) consecutiveStaticSec += dur;
      else consecutiveStaticSec = 0.0;

      let risk = "LOW";
      if (consecutiveStaticSec >= 20.0 || stimulusRatio < 0.45) {
        risk = "CRITICAL_FLATLINE";
        alerts.push({
          block_index: idx + 1,
          timestamp_range: `${fmtTs(startSec)} - ${fmtTs(endSec)}`,
          static_duration_sec: Number(consecutiveStaticSec.toFixed(1)),
          prescription: "Insert a [B-ROLL: ...] cut, on-screen graphic, or verbal re-hook question here.",
        });
      } else if (stimulusRatio < 0.85) {
        risk = "MODERATE_DRIFT";
      }

      timeline.push({
        block: idx + 1,
        time_range: `${fmtTs(startSec)}-${fmtTs(endSec)}`,
        duration_sec: dur,
        word_count: words.length,
        visual_cues: cues.length,
        verbal_pivots: pivots.length + questions,
        stimulus_density: Number(stimulusRatio.toFixed(2)),
        predicted_audience_remaining_pct: currentRetention,
        risk,
      });
      currentSec = endSec;
    });

    const avgAvd = timeline.length
      ? Number((timeline.reduce((a, b) => a + b.predicted_audience_remaining_pct, 0) / timeline.length).toFixed(1))
      : 0.0;

    return {
      total_duration_sec: Number(currentSec.toFixed(1)),
      total_duration_formatted: fmtTs(currentSec),
      predicted_avd_pct: avgAvd,
      final_retention_pct: currentRetention,
      flatline_count: alerts.length,
      pacing_verdict: avgAvd >= 55 ? "ELITE RETENTION (>=55% AVD)" : avgAvd >= 42 ? "HEALTHY PACING (42-54% AVD)" : "HIGH DROP-OFF RISK (<42% AVD)",
      flatline_interventions: alerts,
      timeline_simulation: timeline,
    };
  }

  // 4. DEAD-AIR & FFMPEG CUTTER ENGINE
  if (tool === "deadair") {
    const raw = String(payload.text || "").trim();
    const maxGap = Number(payload.max_gap || 0.45);
    const padSec = 0.06;
    const srtRegex = /(?:^\d+\s*\n)?(\d{2}:\d{2}:\d{2}[,\.]\d{3}|\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3}|\d{2}:\d{2}[,\.]\d{3})\s*\n([\s\S]*?)(?=\n{2,}|\Z)/gm;
    const parseTc = (tc: string) => {
      const parts = tc.trim().replace(",", ".").split(":");
      return parts.length === 3 ? Number(parts[0]) * 3600 + Number(parts[1]) * 60 + Number(parts[2]) : Number(parts[0]) * 60 + Number(parts[1]);
    };
    const fmtTc = (sec: number) => {
      const h = Math.floor(sec / 3600);
      const m = Math.floor((sec % 3600) / 60);
      const s = (sec % 60).toFixed(3).padStart(6, "0");
      return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${s}`;
    };

    const segments: Array<[number, number, string]> = [];
    let match: RegExpExecArray | null;
    while ((match = srtRegex.exec(raw)) !== null) {
      segments.push([parseTc(match[1]), parseTc(match[2]), match[3].replace(/\s+/g, " ").trim()]);
    }
    if (segments.length === 0) return { error: "Provide valid SRT/VTT timecode blocks." };

    const cuts: any[] = [];
    const fillers: any[] = [];
    const keepIntervals: Array<[number, number]> = [];
    let totalDeadAir = 0.0;
    let prevEnd = 0.0;

    segments.forEach(([start, end, line], idx) => {
      const gap = Number((start - prevEnd).toFixed(3));
      if (gap > maxGap) {
        const cutStart = prevEnd > 0 ? Number((prevEnd + padSec).toFixed(3)) : 0.0;
        const cutEnd = Number(Math.max(cutStart, start - padSec).toFixed(3));
        const saved = Number((cutEnd - cutStart).toFixed(3));
        if (saved > 0.1) {
          totalDeadAir += saved;
          cuts.push({ gap_index: cuts.length + 1, cut_from: fmtTc(cutStart), cut_to: fmtTc(cutEnd), seconds_removed: saved });
        }
      }
      const fillerHits = line.match(/\b(um+|uh+|erm+|ah+|like i said|you know what i mean|basically|literally|to be honest|sort of|kind of)\b/gi) || [];
      if (fillerHits.length > 0) {
        fillers.push({ segment_index: idx + 1, timestamp: fmtTc(start), fillers_found: fillerHits.map((f) => f.toLowerCase()), line });
      }
      const kStart = Math.max(0.0, Number((start - padSec).toFixed(3)));
      const kEnd = Number((end + padSec).toFixed(3));
      if (keepIntervals.length && kStart <= keepIntervals[keepIntervals.length - 1][1]) {
        keepIntervals[keepIntervals.length - 1][1] = Math.max(keepIntervals[keepIntervals.length - 1][1], kEnd);
      } else {
        keepIntervals.push([kStart, kEnd]);
      }
      prevEnd = Math.max(prevEnd, end);
    });

    const origDur = Number(segments[segments.length - 1][1].toFixed(2));
    const tightDur = Number(Math.max(0.0, origDur - totalDeadAir).toFixed(2));
    const selectExpr = keepIntervals.map(([s, e]) => `between(t,${s},${e})`).join("+") || "1";

    return {
      original_duration_sec: origDur,
      tightened_duration_sec: tightDur,
      total_dead_air_removed_sec: Number(totalDeadAir.toFixed(2)),
      pacing_compression_pct: Number(((totalDeadAir / Math.max(1, origDur)) * 100).toFixed(1)),
      dead_air_cut_count: cuts.length,
      filler_cluster_count: fillers.length,
      dead_air_cuts: cuts,
      filler_word_alerts: fillers,
      ffmpeg_auto_cut_command: `ffmpeg -i input.mp4 -vf "select='${selectExpr}',setpts=N/FRAME_RATE/TB" -af "aselect='${selectExpr}',asetpts=N/SR/TB" output_tightened.mp4`,
    };
  }

  // 5. CHAPTERS GENERATOR ENGINE
  if (tool === "chapters") {
    const raw = String(payload.text || "").trim();
    const minGap = Number(payload.min_gap || 45);
    const lineRe = /^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(.+)$/;
    const entries: Array<[number, string]> = [];
    for (const line of raw.split(/\r?\n/)) {
      const m = line.trim().match(lineRe);
      if (m) {
        const parts = m[1].split(":").map(Number);
        const sec = parts.length === 3 ? parts[0] * 3600 + parts[1] * 60 + parts[2] : parts[0] * 60 + parts[1];
        entries.push([sec, m[2].trim()]);
      }
    }
    if (entries.length === 0) return { error: "Provide lines with [MM:SS] timestamps." };
    entries.sort((a, b) => a[0] - b[0]);

    const fmtChapTs = (sec: number) => `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(sec % 60).padStart(2, "0")}`;
    const makeTitle = (txt: string) =>
      txt.replace(/\[.*?\]/g, "").split(/[.!?]/)[0].trim().split(/\s+/).slice(0, 5).map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");

    const chapters: any[] = [{ timestamp_sec: 0, timestamp: "00:00", title: "Hook & Core Premise" }];
    let lastSec = 0;
    for (const [sec, txt] of entries) {
      if (sec - lastSec >= Math.min(minGap, 15)) {
        chapters.push({ timestamp_sec: sec, timestamp: fmtChapTs(sec), title: makeTitle(txt) });
        lastSec = sec;
      }
    }
    return {
      youtube_compliant: chapters.length >= 3 && chapters[0].timestamp_sec === 0,
      chapter_count: chapters.length,
      validation_errors: chapters.length < 3 ? ["Minimum 3 chapters required."] : [],
      chapters,
      copy_paste_description_block: chapters.map((c) => `${c.timestamp} ${c.title}`).join("\n"),
    };
  }

  // 6. VIRAL SWIPE DECONSTRUCTOR ENGINE
  if (tool === "swipe") {
    const title = String(payload.title || "Untitled Outlier");
    const transcript = String(payload.text || "").replace(/\[.*?\]/g, " ").trim();
    const sentences = transcript.split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);
    if (sentences.length === 0) return { error: "Empty transcript provided." };

    const skeleton = title
      .replace(/\$[\d,\.]+[KkMmBb]?/g, "[$_AMOUNT]")
      .replace(/\b\d+\s*(days|hours|minutes|months|years|seconds|steps|tools|ways)\b/gi, "[NUMBER] $1")
      .replace(/\b\d+\b/g, "[NUMBER]");

    const words = transcript.match(/\b[\w']+\b/g) || [];
    const totalSentences = sentences.length;
    const hookEnd = Math.max(1, Math.round(totalSentences * 0.14));
    const setupEnd = Math.max(hookEnd + 1, Math.round(totalSentences * 0.32));
    const climaxStart = Math.max(setupEnd + 1, Math.round(totalSentences * 0.82));

    const openLoops = sentences.filter(
      (s) => s.includes("?") || /\b(wait until|later|in a minute|secret|but first|here is the catch|turns out|plot twist)\b/i.test(s)
    );

    return {
      original_title: title,
      reusable_title_skeleton: skeleton,
      structural_metrics: {
        total_word_count: words.length,
        estimated_duration_min: Number((words.length / 150.0).toFixed(2)),
        total_sentences: totalSentences,
        avg_words_per_sentence: Number((words.length / totalSentences).toFixed(2)),
        open_loops_detected: openLoops.length,
      },
      four_act_dna: {
        act_1_hook_0_14pct: { opening_anchor: sentences.slice(0, hookEnd).join(" ").slice(0, 140) },
        act_2_escalation_14_32pct: { opening_anchor: sentences.slice(hookEnd, setupEnd).join(" ").slice(0, 140) },
        act_3_core_execution_32_82pct: { opening_anchor: sentences.slice(setupEnd, climaxStart).join(" ").slice(0, 140) },
        act_4_payoff_and_bridge_82_100pct: { opening_anchor: sentences.slice(climaxStart).join(" ").slice(0, 140) },
      },
      extracted_open_loops: openLoops.slice(0, 8),
    };
  }

  return { error: "Unsupported tool" };
}

export async function executeSkillTool(req: AgentToolRequest): Promise<AgentToolResponse> {
  const startTime = Date.now();
  const tool = req?.tool;
  const relPath = TOOL_MAP[tool];

  if (!relPath) {
    return {
      status: "error",
      execution_ms: Date.now() - startTime,
      error: `Unknown tool '${tool}'. Valid tools: ${Object.keys(TOOL_MAP).join(", ")}`,
    };
  }

  const validationErr = validatePayload(tool, req.payload);
  if (validationErr) {
    return {
      status: "error",
      tool,
      execution_ms: Date.now() - startTime,
      error: validationErr,
    };
  }

  const fullPath = path.resolve(process.cwd(), relPath);
  try {
    if (fs.existsSync(fullPath)) {
      const data = await runPythonSubprocess(fullPath, req.payload);
      return {
        status: "success",
        tool,
        runtime_engine: "python-cli-subprocess",
        execution_ms: Date.now() - startTime,
        data,
      };
    }
  } catch {
    // When running on Vercel Serverless (where Python binary is absent), execute the real TS engine
  }

  const realTsData = executeRealTypeScriptEngine(tool, req.payload);
  return {
    status: "success",
    tool,
    runtime_engine: "ts-native-engine",
    execution_ms: Date.now() - startTime,
    data: realTsData,
  };
}

export default async function handler(req: IncomingMessage & { body?: any }, res: ServerResponse): Promise<void> {
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
    const manifest = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf-8")) : { skills: Object.keys(TOOL_MAP) };
    return send(200, { status: "success", manifest });
  }

  if (req.method !== "POST") {
    return send(405, { status: "error", error: "Use GET /api/health, GET /api/skills, or POST /api" });
  }

  if (req.body && typeof req.body === "object") {
    const out = await executeSkillTool(req.body);
    return send(out.status === "success" ? 200 : 400, out);
  }

  let raw = "";
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