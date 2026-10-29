import { Request, Response } from 'express';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';

const execPromise = util.promisify(exec);

export default async function handler(req: Request, res: Response) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed. Use POST.' });
  }

  const { action, nicheKey, scriptContent } = req.body;

  if (!action) {
    return res.status(400).json({ error: 'Missing required field: action' });
  }

  try {
    let scriptName = '';
    let pyArgs = '';

    switch (action) {
      case 'get_unique_topic':
        scriptName = 'anti_duplicate.py';
        pyArgs = `"${nicheKey || 'kids_cartoons'}"`;
        break;
      case 'humanize_script':
        scriptName = 'human_pacing.py';
        pyArgs = `"${scriptContent || ''}"`;
        break;
      case 'score_hook':
        scriptName = 'hookscore.py';
        pyArgs = `"${scriptContent || ''}"`;
        break;
      case 'optimize_retention':
        scriptName = 'retention.py';
        pyArgs = `"${scriptContent || ''}"`;
        break;
      case 'generate_chapters':
        scriptName = 'chapters.py';
        pyArgs = `"${scriptContent || ''}"`;
        break;
      case 'optimize_title':
        scriptName = 'title.py';
        pyArgs = `"${nicheKey || 'kids_cartoons'}"`;
        break;
      default:
        return res.status(400).json({ error: 'Invalid action specified.' });
    }

    const scriptPath = path.join(process.cwd(), 'skills', getFolderForAction(action), scriptName);
    const command = `python3 "${scriptPath}" ${pyArgs}`;

    const { stdout, stderr } = await execPromise(command);

    if (stderr && !stdout) {
      throw new Error(stderr);
    }

    let parsedResult;
    try {
      parsedResult = JSON.parse(stdout);
    } catch {
      parsedResult = { output: stdout.trim() };
    }

    return res.status(200).json({
      success: true,
      action,
      data: parsedResult
    });

  } catch (error: any) {
    return res.status(500).json({
      success: false,
      error: error.message || 'Internal Server Error during execution.'
    });
  }
}

function getFolderForAction(action: string): string {
  switch (action) {
    case 'get_unique_topic': return 'yt-script';
    case 'humanize_script': return 'yt-script';
    case 'score_hook': return 'yt-script';
    case 'optimize_retention': return 'yt-retention';
    case 'generate_chapters': return 'yt-chapters';
    case 'optimize_title': return 'yt-package';
    default: return 'yt-audit';
  }
}