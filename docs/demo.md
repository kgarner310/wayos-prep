# WAYOS PREP — Demo Script (Outlook Add-in)

## Setup

1. Start all services: `cd infra && docker compose up --build`
2. Sideload the add-in into Outlook (see README for instructions)
3. Or open `http://localhost:3000` in a browser for standalone mode

## Demo 1: Prep This Account (Primary Demo)

1. Open Outlook and click **WAYOS PREP** in the ribbon
2. The task pane opens on the right side
3. Click **Prep This Account**
4. Select **Roofing** from the industry picker
5. Enter Location: **North Carolina**
6. Enter Employees: **12**
7. Enter MOD: **1.15**
8. Enter Vehicle Exposure: **3 trucks**
9. Click **Generate Brief**
10. Review the full Client Brief in the task pane
11. Click **Copy Brief** to copy to clipboard
12. Click **Send Pack (Email)**
13. Click **Underwriter Email** — a new Outlook compose window opens with subject and body pre-filled
14. Click **Internal Note (CSR)** — another compose window with CSR summary
15. Rate the brief with the feedback buttons

## Demo 2: Calendar Auto-Detect

1. Create a calendar invite: "Meeting with ABC Roofing - Raleigh NC"
2. Open the calendar invite
3. Click **WAYOS PREP** in the ribbon
4. The add-in detects "ABC Roofing" from the subject
5. Shows "From your calendar" card with a **Prep This Meeting** button
6. One click generates a brief

## Demo 3: Ask Risk Question

1. From the task pane Home, click **Ask Risk Question**
2. Type: "What risks should I discuss with a trucking company?"
3. Optionally add location: "Texas"
4. Click **Generate Brief**
5. Use Send Pack to email the underwriter directly from Outlook

## Demo 4: Industry Lookup

1. Click **Industry Lookup**
2. Search for "restaurant"
3. Click **Restaurants**
4. Review the full risk profile
5. Click **Generate Brief**

## Key Talking Points

- "The producer never leaves Outlook. The brief generates right here in the task pane."
- "Send Pack opens a new email — subject line, body, everything pre-formatted. Hit send."
- "Open a calendar invite, click WAYOS PREP, and the system reads the meeting subject to suggest the industry."
- "This works with zero API keys. The risk data is curated, not hallucinated."
- "A producer can prep for a meeting in 30 seconds without opening a new app."

## Why Outlook

- Producers live in Outlook — email to underwriters, CSRs, and clients
- No new app to install, no new login, no new workflow
- IT can deploy via Microsoft 365 admin center to the entire agency
- Calendar integration means every meeting becomes a prep opportunity

## Demo Data Highlights

- **Roofing**: Falls from height, hail belt exposure, completed operations
- **Trucking**: Nuclear verdicts, CSA scores, cargo liability
- **Restaurants**: Liquor liability, foodborne illness, kitchen burns
- **Daycare**: Abuse/molestation coverage, staff ratios, transport liability
- **Assisted Living**: Patient lifting injuries, elopement risk, medication errors
