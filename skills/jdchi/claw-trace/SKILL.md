---
name: claw-trace
license: MIT
description: |
  Track and visualize the OpenClaw agent's work process. Record tool call inputs, outputs, duration, and status, and present them in an easy-to-read format.
  Triggered when user asks to view work process, call history, or tool usage records.
  Also used for visualizing AI thinking process and decision steps.
  Only applicable to OpenClaw platform.
---

# Claw Trace - Work Process Visualization

This Skill is used to record and display the AI agent's work process.

## Feature Modules (Configurable)

User can say "enable XX feature" or "use simple mode" to switch.

### Module 1: Call Table (Enabled by Default)

| Step | Tool | Input | Result | Duration |
|------|------|-------|--------|----------|
| 1 | web_search | query: "xxx" | ❌ Failed | 0ms |
| 2 | web_fetch | url: "xxx" | ✅ Success | 230ms |

### Module 2: Flowchart (Enabled by Default)

[User Request]
    ↓
1. web_search → ❌
    ↓
2. web_fetch → ✅
    ↓
[Reply to User]

### Module 3: Statistics (Optional)

```
📊 Work Statistics
⏱️ Total Time: 8.5s
🔧 Tool Calls: 15 times
✅ Success Rate: 87% (13/15)

📈 Tool Usage Ranking:
  1. web_fetch  - 10 times (67%)
  2. exec       - 3 times (20%)
```

### Module 4: Detailed Log (Optional)

Record complete input/output for each call (except sensitive info).

### Module 5: Save to File (Optional)

Generate Markdown report saved to workspace.

## Usage

### Configuration File

The Skill has a config file `config.json` with the following options:

```json
{
  "enable": false,        // Whether to enable by default (default: false, on-demand)
  "mode": "simple",       // Mode: simple / full
  "enabledModules": {
    "table": true,        // Call table
    "flowchart": true,   // Flowchart
    "statistics": false,  // Statistics
    "detailedLog": false,// Detailed log
    "saveToFile": false  // Save to file
  },
  "language": "auto"       // Language: auto / zh / en
}
```

### User Commands

User can modify config through conversation:

| Command | Action |
|---------|--------|
| "enable trace" | enable = true |
| "disable trace" | enable = false |
| "use simple mode" | mode = simple |
| "use full mode" | mode = full |
| "enable statistics" | statistics = true |
| "output in English" | language = en |
| "output in Chinese" | language = zh |

### Workflow

1. **Each time Skill is called**: Read `config.json` first to get current config
2. **Based on config**:
   - enable = false → Don't show (unless user explicitly requests)
   - enable = true → **Must show**, output according to mode and enabledModules
3. **When user modifies config**: Update config.json and save

### ⚠️ Important Rule

**When enable = true, trace output MUST be included in every reply after tool calls, do not omit!**

### Language Auto-Detection

- Output language follows user's language
- User speaks Chinese → Output in Chinese
- User speaks English → Output in English

## Notes

- Sensitive info (API Keys, passwords) should not be recorded
- Truncate overly long output with [...]
- Clearly indicate reasons for failed calls
- Keep output concise, don't over-detail
