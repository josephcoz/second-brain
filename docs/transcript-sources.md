# Meeting Transcript Sources

The nightly journal agent pulls meeting content from multiple sources. This document explains each source and how they are prioritized.

## Google Drive (Primary)

Google Meet automatically saves transcripts as Google Docs in your Drive. These are the highest-fidelity source because they contain full verbatim text with speaker attribution.

- **Location**: Google Drive, typically in a "Meet Recordings" or "Meet Transcripts" folder
- **Access**: Via Google Drive MCP tools — search for docs matching the meeting title or date
- **Format**: Plain text with speaker labels and timestamps
- **Pros**: Full transcript, speaker-attributed, searchable
- **Cons**: Only available for Google Meet calls; may take a few minutes to appear after the meeting ends

## Granola (Default Backup)

Granola captures meetings across platforms and generates AI summaries. It serves as the fallback when a full Google Drive transcript is not available.

- **Location**: Granola app, accessed via the Granola MCP server
- **Access**: `list_meetings` to find today's meetings, `get_meeting_transcript` for content
- **Format**: AI-generated summary with key points, action items, and attendee list
- **Pros**: Works across Zoom, Meet, Teams; always generates a summary even if transcript is unavailable
- **Cons**: AI-summarized (not verbatim); may miss nuance or specific quotes

## Source Prioritization

The nightly journal agent follows this priority order when gathering meeting content:

1. **Google Drive transcript** — if a full transcript exists, use it as the primary source. Extract key quotes, decisions, and action items.
2. **Granola summary** — if no Drive transcript is found, use the Granola summary. Note in the journal that the source is an AI summary.
3. **Granola + Drive combined** — when both exist, use the Drive transcript for verbatim content and the Granola summary for its structured action items and key points.
4. **Manual notes** — if neither automated source is available (e.g., in-person meeting), the journal entry notes the meeting occurred with whatever context is available from calendar data.

The data gathering script (`nightly-journal.sh`) checks for pre-existing meeting files in the vault's `Meetings/` directory. The agent then supplements with live MCP calls to Granola and Google Drive for any meetings not yet captured.
