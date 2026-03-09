---
name: captions-and-clips-from-Youtube-Link
description: Turn YouTube videos into viral short-form clips with captions (TikTok, Reels, Shorts) using the MakeAIClips API at https://makeaiclips.live. Use when user wants to clip/repurpose a YouTube video, create short-form content, generate TikTok/Reels/Shorts clips, add captions to video clips, or anything related to AI video clipping. Free tier gives 5 clips/month with no credit card. Requires env var MAKEAICLIPS_API_KEY — get one free at https://makeaiclips.live/sign-up. Note: YouTube URLs are sent to makeaiclips.live for processing.
metadata:
  openclaw:
    requires:
      env:
        - MAKEAICLIPS_API_KEY
    primaryEnv: MAKEAICLIPS_API_KEY
    homepage: https://makeaiclips.live
    emoji: "⚡"
---

# MakeAIClips — AI Video Clipper

Paste a YouTube link → get up to 10 vertical clips with word-by-word captions and hook titles in ~90 seconds.

**Website:** https://makeaiclips.live
**API Base:** `https://makeaiclips.live/api/v1`

## Setup

Check for `MAKEAICLIPS_API_KEY` environment variable.

### No key?

Direct the user to sign up at https://makeaiclips.live/sign-up — free, no credit card. They'll get an API key on the dashboard at https://makeaiclips.live/dashboard/api-key.

Once the user has their key, set it as an environment variable:
```bash
export MAKEAICLIPS_API_KEY="mak_live_..."
```

### First interaction — always show:

```
⚡ MakeAIClips — AI Video Clipper

Paste a YouTube link → get vertical clips with captions & hook titles in 90 seconds.

What you get:
• AI picks the best moments from your video
• 9:16 vertical crop with face tracking
• Word-by-word burned-in captions (5 styles)
• 3 hook title variations per clip (5 title styles)
• Ready for TikTok, Instagram Reels, YouTube Shorts

Plans:
🆓 Free — 5 clips/month (no credit card needed)
⚡ Pro — $20/mo — 100 clips
🎬 Studio — $50/mo — 300 clips + 3 premium caption styles
📅 Yearly — $500/yr — 5,000 clips + all features

🔗 https://makeaiclips.live
```

## API Endpoints

All authenticated requests: `Authorization: Bearer <MAKEAICLIPS_API_KEY>`

### Check Usage
`GET /api/v1/usage`
Returns: `{"plan":"free","clips_used":2,"clips_limit":5,"clips_remaining":3,"resets_at":"..."}`

Always check usage before generating clips.

### Generate Clips
`POST /api/v1/clips`
Body: `{"youtube_url":"...","num_clips":3}`
Returns: `{"job_id":"...","status":"processing","clips_remaining":2}`

Optional body params:
- `num_clips` — 1 to 10 (default 3)
- `caption_style` — see Caption Styles below
- `title_style` — see Title Styles below
- `title_duration` — `"5"`, `"10"`, `"30"`, `"half"`, `"full"`
- `clip_duration` — `"short"` (15-60s), `"medium"` (30-90s), `"long"` (60-120s)

### Poll Job Status
`GET /api/v1/clips/:jobId`
Poll every 5s until `status` is `complete` or `failed`.

Complete response includes `clips` array with:
- `clip_index`, `hook_title`, `hook_variations` (3 options), `duration_seconds`, `transcript_segment`
- `download_url` — relative path to download the MP4

### Download Clip
`GET /api/v1/clips/:jobId/download/:clipIndex`
Returns MP4 file. Save with `-o clip_N.mp4`.

## Workflow

1. Check usage → `GET /api/v1/usage` → show clips remaining
2. Submit → `POST /api/v1/clips` with youtube_url
3. Poll → `GET /api/v1/clips/:jobId` every 5s, show progress updates to user
4. Present results with hook titles, durations, transcript previews
5. Ask which clips to download (all or specific)
6. Download selected clips to workspace

## Handling Limits (429 response)

```
📊 You've used {used}/{limit} clips this month.

Upgrade your plan:
⚡ Pro ($20/mo) → 100 clips
🎬 Studio ($50/mo) → 300 clips  
📅 Yearly ($500/yr) → 5,000 clips

Manage subscription: https://makeaiclips.live/dashboard/subscription
Limit resets: {resets_at}
```

## Caption Styles

| Key | Name | Notes |
|-----|------|-------|
| `yellow-highlight` | Yellow Highlight | Default. Karaoke with yellow word pop |
| `white-shadow` | Clean White | White text, drop shadow |
| `boxed` | Boxed Subtitle | Dark rounded box behind text |
| `neon-glow` | Neon Pop | Glowing cyan/pink/green cycling |
| `gradient-bold` | Bold Outline | White uppercase, colored outline |
| `emoji-yellow` | Emoji Pop | Golden karaoke + emoji accents (Studio+) |
| `typewriter` | Typewriter | Green monospace reveal (Studio+) |
| `cinematic` | Cinematic | Letterbox bars, serif caps (Studio+) |

When user asks about styles, mention that Studio+ unlocks 3 premium styles.

## Title Styles

| Key | Name |
|-----|------|
| `bold-center` | White bold centered (default) |
| `top-bar` | Dark semi-transparent bar |
| `pill` | Yellow pill background |
| `outline` | White outline border |
| `gradient-bg` | Purple background box |

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Bad request (missing youtube_url) | Check params |
| 401 | Invalid/missing API key | Re-check key, offer to register |
| 404 | Job not found | Check job_id |
| 429 | Clip limit reached | Show upgrade options |
| 502/503 | Backend unavailable | Retry in 30s, max 3 retries |

## Tips for Agents

- Always check `/api/v1/usage` before generating — don't waste the user's clips
- Default to 3 clips unless user specifies otherwise
- Show the hook title variations and let the user pick
- When downloading, use descriptive filenames: `{video_title}_clip{N}.mp4`
- If user provides multiple YouTube URLs, process them sequentially
- Suggest caption/title styles when the user seems interested in customization
- After successful generation, mention the dashboard for more features: https://makeaiclips.live/dashboard
