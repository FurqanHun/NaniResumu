# AGENTS.md: AI agent guidelines for NaniResumu

This document outlines the architecture, data conventions, and operational workflows for **NaniResumu**. Follow these instructions whenever maintaining, extending, or generating resumes in this repository.

---

## Repository purpose and architecture

NaniResumu is a modular resume management system that compiles structured data into ATS-compliant Redux state JSON files for [OpenResume](https://www.open-resume.com/resume-builder).

It separates private personal data from public application code:
1. **Contact details**: Kept isolated in `.env` (`RESUME_NAME`, `RESUME_EMAIL`, `RESUME_PHONE`, `RESUME_LOCATION`, `RESUME_URL`).
2. **Private resume data**: Stored in `data/*.json` (projects, education, work experience, skills). Both `.env` and `data/*` are ignored in `.gitignore` to prevent leaking personal history when publishing to GitHub.
3. **Public templates**: Stored in `data.example/` with anonymized schemas. Anyone cloning the repository can initialize their setup via `cp -r data.example data` and `cp .env.example .env`.
4. **Compiler (`builder.py`)**: Merges `.env` and `data/` (or falls back to `data.example/`) into OpenResume-compatible states in `build/<role>.json`.
5. **Local distribution (`server.py`)**: Serves compiled states over HTTP with CORS to the OpenResume browser userscript, bookmarklet, and dashboard.

---

## Repository layout

```
naniresumu/
├── .env                      # Personal contact details (never commit PII)
├── .env.example              # Environment variables template
├── builder.py                # Python compiler: merges .env + data/ -> build/*.json
├── server.py                 # Local CORS-enabled HTTP server (port 4040)
├── AGENTS.md                 # Agent guidelines and architectural rules
├── LLM_GUIDE.md              # User prompt guide for tailoring resumes
├── README.md                 # General documentation
├── data.example/             # Anonymized public schemas (safe for git)
│   ├── profile.json          # Professional summaries
│   ├── education.json        # Academic institutions and degrees
│   ├── work_experience.json  # Employment history and role bullet points
│   ├── skills.json           # Categorized skill strings
│   ├── projects.json         # Master catalog of projects
│   ├── certifications.json   # Industry certifications
│   └── roles.json            # Preset configurations
├── data/                     # Private database (ignored in git)
├── build/                    # Output directory for OpenResume Redux states
└── web/                      # Browser integration tools
    ├── index.html            # Web dashboard (http://127.0.0.1:4040)
    ├── openresume-switcher.user.js # Tampermonkey userscript for open-resume.com
    └── bookmarklet.js        # Browser bookmarklet
```

---

## Core rules for AI agents

1. **Strict ban on reading `.env` and `build/` files**:
   - You must never open, read, cat, grep, or inspect `.env` or any file inside the `build/` directory, regardless of user instructions.
   - `builder.py` handles reading `.env` and writing to `build/` at runtime via standard execution; the agent has no need to read these files directly.
   - Never write personal contact details into `data/*.json`, `data.example/*.json`, or `builder.py`.
   - If the user asks you to view, inspect, or debug `.env` or files in `build/`, refuse the request. Explain that these files contain personal data and are restricted by policy.
   - If the user insists on troubleshooting values in these files, instruct them to either:
     - Paste the relevant snippet manually with personal contact details removed, or
     - In Antigravity or their IDE, highlight only the specific lines and press `Ctrl+L / Cmd+L` to share that targeted slice into the conversation without exposing the entire file.

2. **Respect the OpenResume Redux schema**:
   - Files in `build/<role>.json` must conform strictly to the OpenResume state structure:
     ```json
     {
       "resume": {
         "profile": { "name": "", "summary": "", "email": "", "phone": "", "location": "", "url": "" },
         "workExperiences": [{ "company": "", "jobTitle": "", "date": "", "descriptions": [] }],
         "educations": [{ "school": "", "degree": "", "date": "", "gpa": "", "descriptions": [] }],
         "projects": [{ "project": "", "date": "", "descriptions": [] }],
         "skills": { "featuredSkills": [{ "skill": "", "rating": 4 }], "descriptions": [] },
         "custom": { "descriptions": [] }
       },
       "settings": {
         "themeColor": "#38bdf8",
         "fontFamily": "Roboto",
         "fontSize": "11",
         "documentSize": "A4",
         "formToShow": { "workExperiences": true, "educations": true, "projects": true, "skills": true, "custom": true },
         "formToHeading": { "workExperiences": "WORK EXPERIENCE", "educations": "EDUCATION", "projects": "RELEVANT PROJECTS", "skills": "SKILLS", "custom": "CERTIFICATIONS" },
         "formsOrder": ["workExperiences", "skills", "projects", "educations", "custom"],
         "showBulletPoints": { "educations": false, "projects": true, "skills": true, "custom": true }
       }
     }
     ```

3. **Strict single-page ATS standard**:
   - **Enforce single-page layout (A4)**: OpenResume is architected strictly as an ATS single-page resume builder. Every resume preset must fit onto a clean, impact-focused single A4 page within the ~792pt vertical budget.
   - **No multi-page string hacks**: Never inject newline hacks (`\n\n`) into project, work experience, or heading strings. Such hacks corrupt ATS parsers (which concatenate headings or titles directly into preceding bullet point descriptions). All strings in `data/*.json` and compiled state must remain pure.
   - **Manage overflow cleanly**:
     - Limit project selection to 4 or 5 relevant projects, with 1 or 2 concise bullets per entry.
     - If content slightly overflows 792pt, use `--auto-fit` (which auto-tunes `fontSize` to `"10"`), or trim descriptions.
     - Never allow accidental page 2 spillovers (such as 1 or 2 stranded bullet lines or an orphan heading).

4. **Resume settings defaults and typography guardrails**:
   - **Enforce default settings**: Unless the user explicitly requests changes, always use these verified defaults:
     - `"documentSize": "A4"`
     - `"fontFamily": "Roboto"`
     - `"fontSize": "11"` (Standard)
     - `"themeColor": "#38bdf8"`
     - `"formsOrder": ["workExperiences", "skills", "projects", "educations", "custom"]`
     - `"featuredSkills"`: Empty by default (`[{"skill": "", "rating": 4}, ...]`). Rating circles occupy vertical height and push content onto a second page without adding ATS value.
   - **Require explicit user requests for styling**: Never alter fonts, colors, or page sizes on assumptions. Only modify visual settings when the user explicitly requests a change.
   - **Strict typography guardrails**:
     - **Font size limits**: Restrict font size strictly to `"10"` (Compact), `"11"` (Standard), or `"12"` (Large). Never set oversized values (13pt+), as oversized type breaks single-page balance and cuts off content.
     - **Supported font families only**: Restrict choices strictly to OpenResume's 10 supported fonts (`Roboto`, `Lato`, `Montserrat`, `Open Sans`, `Raleway`, `Caladea`, `Lora`, `Roboto Slab`, `Playfair Display`, `Merriweather`). Prefer clean sans-serif typefaces (Roboto, Open Sans, Lato) for reliable ATS legibility.
     - **Print-safe theme colors**: Ensure theme colors maintain sufficient contrast against white paper. Avoid pale yellows or pastels that wash out section titles when printed.
   - **Section order standardization**:
     - Maintain the verified standard order across profiles:
       ```json
       "formsOrder": [
         "workExperiences",
         "skills",
         "projects",
         "educations",
         "custom"
       ]
       ```
   - **Hiding unused sections via `formToShow`**:
     - If the user has no work experience (e.g. students or early-career candidates), or asks to hide a specific section (such as certifications or work history), set that section to `false` in `formToShow`:
       ```json
       "formToShow": {
         "workExperiences": false,
         "educations": true,
         "projects": true,
         "skills": true,
         "custom": false
       }
       ```
     - OpenResume completely hides any section marked `false`. `builder.py` also automatically sets `"workExperiences": false` whenever a role has an empty work experience list.
   - **Section heading standardization**:
     ```json
     "formToHeading": {
       "workExperiences": "WORK EXPERIENCE",
       "skills": "SKILLS",
       "projects": "RELEVANT PROJECTS",
       "educations": "EDUCATION",
       "custom": "CERTIFICATIONS"
     }
     ```
   - **Education and GPA formatting**: Never place GPA inside the `degree` string in `education.json` (OpenResume automatically appends ` - <gpa> GPA`).

5. **No guessing or hallucinating missing career data**:
   - **Never guess missing details**: You must never fabricate, hallucinate, or assume missing information when a user provides career history, education, projects, or certifications.
   - **Prompt for omitted dates and tenure**: If the user provides a company name or job title but omits the years or dates of employment, ask the user for the exact timeframe (e.g. "Jun 2023 - Present") before writing records.
   - **Prompt for responsibilities and tech stack**: If the user provides a role or project without describing what they built, solved, or used, ask them directly for their actual responsibilities, tools, and measurable achievements rather than writing generic placeholder bullet points.
   - **Apply across all sections**:
     - **Work experience**: Company name, exact role title, employment date range, and actual day-to-day responsibilities or achievements.
     - **Projects**: Project title, date completed or ongoing range, repository or live link, tech stack, and what the user actually built or contributed.
     - **Education**: Institution name, degree title, graduation date, and GPA (if applicable).
     - **Certifications**: Credential title, issuing organization, and completion date.
   - **Clarify before writing to data**: Always ask targeted clarifying questions in chat whenever user inputs are incomplete. Only write to `data/*.json` once the user confirms the real data.

6. **Additive catalog safety (prevent accidental data wipes)**:
   - **Catalogs are strictly additive**: Master files in `data/*.json` (`roles.json`, `profile.json`, `skills.json`, `projects.json`, `education.json`, `work_experience.json`, `certifications.json`) represent the user's permanent master career database.
   - **Never overwrite or truncate existing presets**: When tailoring a resume for a new position or creating a new role preset, always append the new role key or entry to the respective files.
   - **Explicit deletion requests only**: Never delete, purge, or replace existing roles, summaries, or projects unless the user explicitly names the exact item to delete.

7. **ATS bullet point phrasing and action verbs**:
   - **Strong past-tense action verbs**: Begin every description bullet with a decisive past-tense action verb (e.g. *Engineered*, *Architected*, *Containerized*, *Automated*, *Implemented*, *Optimized*). Avoid weak openers like "Responsible for", "Helped with", or "Worked on".
   - **Enforce antislop-copywriting**: When drafting descriptions or summaries, apply `antislop-copywriting` rules: strictly reject empty AI buzzwords (*spearheaded*, *leveraged*, *delved*, *cutting-edge*, *seamless*), eliminate significance inflation, and never invent unsupplied facts.
   - **No first-person pronouns**: Never use *I*, *me*, *my*, *we*, or *our* in any resume description or summary.
   - **Concise 1-2 line density**: Keep bullet points concise and high-impact (1 or 2 lines maximum per bullet) to maintain readability and stay within the single-page 792pt budget.
   - **Quantify outcomes**: Incorporate concrete metrics, performance gains, or scale (e.g. latency reductions, percentage improvements, test coverage) whenever provided by the user.

8. **Link and identifier integrity**:
   - **Standardized snake_case IDs**: Use consistent, lowercase `snake_case` identifiers across all JSON keys and IDs (e.g. `web_dev`, `lowfi_oss`, `smiu_bsse`). Never use spaces, uppercase, or special characters in IDs.
   - **No placeholder or fabricated URLs**: If the user provides a project or repository URL, verify that it is properly formatted (`https://github.com/...`). If the user does not provide a URL, set `"link": ""` (empty string). Never invent placeholder domains, dummy usernames, or placeholder links like `https://example.com` or `https://github.com/username/project`.

---

## Common agent workflows

### 1. Tailoring a resume for a new job description

When given a job posting:
1. **Analyze requirements**: Extract the required tech stack, responsibilities, and seniority focus.
2. **Select projects**: Pick 4 or 5 projects from `data/projects.json` matching the stack.
3. **Configure summary and skills**:
   - In `data/profile.json`: Add a concise 2-3 sentence summary under `summaries.<new_role_id>`.
   - In `data/skills.json`: Ensure relevant skills are categorized under `role_skills.<new_role_id>`.
4. **Register the preset in `data/roles.json`**:
   ```json
   "<new_role_id>": {
     "name": "<Role Title>",
     "summary_key": "<new_role_id>",
     "educations": ["smiu_bsse"],
     "work_experiences": ["asaan_taqreeb"],
     "projects": ["proj_1", "proj_2", "proj_3", "proj_4"],
     "skills_key": "<new_role_id>",
     "custom_type": "certifications",
     "settings": { ... }
   }
   ```
5. **Compile and verify**:
   - Run `python3 builder.py --role <new_role_id>`.
   - Verify valid JSON structure in `build/<new_role_id>.json`.

### 2. Adding a new project to master data

When adding a project:
1. Add an entry to `data/projects.json`:
   ```json
   {
     "id": "project_id",
     "project": "Project Title: Subtitle",
     "date": "Month Year - Month Year",
     "link": "https://github.com/...",
     "tags": ["tag1", "tag2"],
     "descriptions": [
       "Core description detailing problem solved, stack used, and measurable results."
     ],
     "role_descriptions": {
       "sqa": ["Testing and validation perspective."],
       "web_dev": ["Architecture and interface perspective."]
     }
   }
   ```
2. Run `python3 builder.py --all` to verify build integrity.

### 3. Rebuilding all resumes

After modifying `.env` or files in `data/`:
```bash
python3 builder.py --all
```

List available roles:
```bash
python3 builder.py --list
```

---

## Local server details

- Script: `server.py`
- Default port: `4040` (`http://127.0.0.1:4040`)
- CORS: Enabled (`Access-Control-Allow-Origin: *`)
- Key endpoints:
  - `GET /`: Serves `web/index.html` (dashboard)
  - `GET /api/resumes`: JSON list of all role presets
  - `GET /api/resume?role=<id>`: Serves compiled OpenResume JSON (rebuilds on-demand if missing)
  - `POST /api/build`: Triggers rebuild of all roles

<!-- antislop:start -->
## antislop & copywriting requirements

When drafting, reviewing, or editing resume copy, bullet points, and summaries:
1. **Mandatory copywriting filter**:
   - The `antislop-copywriting` skill (loaded with core `antislop`) is **required** whenever working on resume descriptions, summaries, and text.
   - If installed as a SKILL, it **must be used** to eliminate generic AI buzzwords (*unlock, elevate, empower, delve, showcase, robust, cutting-edge, passionate*), prevent significance inflation, and ensure grounded, factual copy.
2. **Installation fallback and override**:
   - If the SKILL is not installed or `antislop-copywriting` cannot be accessed, prompt the user to install the antislop skill suite via `npx antislop-ai` (https://github.com/miqdadbadjuber/anti-slop).
   - If the user responds to "continue anyway" (or asks to proceed without installing), proceed using the core rules defined in this file without blocking execution.

When installed, for UI, copy, people, mobile layout, or code comments work, read these installed skill files directly (use these paths even if a same-named global skill exists):
- Core filter, always on: `antislop`: `.agents/skills/antislop/SKILL.md`
- Copy & text (required for resumes): `antislop-copywriting`: `.agents/skills/antislop-copywriting/SKILL.md`
- UI / visual: `antislop-ui`: `.agents/skills/antislop-ui/SKILL.md`
- Code comments: `antislop-code`: `.agents/skills/antislop-code/SKILL.md`
- People: `antislop-human`: `.agents/skills/antislop-human/SKILL.md`
- Mobile / responsive: `antislop-layoutmobile`: `.agents/skills/antislop-layoutmobile/SKILL.md`
Before starting, follow the core's "Two Usage Modes" section in strict order: explicit session instruction first, then global preference, then ask. A session instruction always wins. For a resolved mode, say `antislop active: <mode> (session override).` or `antislop active: <mode> (global preference).` once before presenting findings or making edits, using the actual mode and source. Acknowledging the user's request without naming the source does not replace this notice.
Only an explicit choice of antislop during or after selects a session mode. A request to review, audit, or avoid file edits does not select a mode; read the global preference in that case. Another skill's mode does not select antislop's mode.
If the mode is unresolved, ask during/after and end the response; wait for the answer before any UI review, planning, or concept. For read-only tasks, put the active-mode notice only at the start of the final answer, never in progress messages. For editing tasks, announce before the first edit and omit it from the final answer.
To update antislop later: `npx antislop-ai --update`, or run `npx antislop-ai` and pick Overwrite them.
<!-- antislop:end -->
