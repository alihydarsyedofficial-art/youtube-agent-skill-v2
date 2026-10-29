"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = handler;
const { exec } = require('child_process');
const util = require('util');
const path = require('path');
const execPromise = util.promisify(exec);
async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed. Use POST.' });
    }
    const body = req.body ?? {};
    const { action, nicheKey, scriptContent } = body;
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
        }
        catch {
            parsedResult = { output: stdout.trim() };
        }
        return res.status(200).json({
            success: true,
            action,
            data: parsedResult
        });
    }
    catch (error) {
        return res.status(500).json({
            success: false,
            error: error.message || 'Internal Server Error during execution.'
        });
    }
}
function getFolderForAction(action) {
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
