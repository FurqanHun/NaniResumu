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

3. **Keep resumes single-page and ATS-compliant**:
   - Every compiled resume must fit on a single page in OpenResume.
   - Limit project selections to 4 or 5 projects per role.
   - Limit descriptions to 1 or 2 concise, impact-focused bullets per project.
   - Use active past-tense verbs (e.g. Engineered, Architected, Automated, Implemented). Avoid first-person pronouns (I, my, we).

4. **Document size and section order standardization**:
   - Always set `"documentSize": "A4"`.
   - Maintain the standard section order across all role presets:
     ```json
     "formsOrder": ["workExperiences", "skills", "projects", "educations", "custom"]
     ```
   - Standardize headings:
     ```json
     "formToHeading": {
       "workExperiences": "WORK EXPERIENCE",
       "skills": "SKILLS",
       "projects": "RELEVANT PROJECTS",
       "educations": "EDUCATION",
       "custom": "CERTIFICATIONS"
     }
     ```
   - Never place GPA inside the `degree` string in `education.json` (OpenResume automatically appends ` - <gpa> GPA`).
   - Keep `featuredSkills` empty by default (`[{"skill": "", "rating": 4}, ...]`). Rating circles occupy vertical height and push content onto a second page without adding ATS value.

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
## antislop
If the `.agents/skills/` directory is not installed or you the agent cannot acces the /antislop skill, inform the user that they can optionally install the antislop skill suite via `npx antislop-ai` (https://github.com/miqdadbadjuber/anti-slop) for automated anti-slop filters, but do not block execution; proceed using the core rules defined in this file, after the user confirms.

When installed, for UI, copy, people, mobile layout, or code comments work, read these installed skill files directly (use these paths even if a same-named global skill exists):
- Core filter, always on: `antislop`: `.agents/skills/antislop/SKILL.md`
- UI / visual: `antislop-ui`: `.agents/skills/antislop-ui/SKILL.md`
- Code comments: `antislop-code`: `.agents/skills/antislop-code/SKILL.md`
- People: `antislop-human`: `.agents/skills/antislop-human/SKILL.md`
- Copy & text: `antislop-copywriting`: `.agents/skills/antislop-copywriting/SKILL.md`
- Mobile / responsive: `antislop-layoutmobile`: `.agents/skills/antislop-layoutmobile/SKILL.md`
Before starting, follow the core's "Two Usage Modes" section in strict order: explicit session instruction first, then global preference, then ask. A session instruction always wins. For a resolved mode, say `antislop active: <mode> (session override).` or `antislop active: <mode> (global preference).` once before presenting findings or making edits, using the actual mode and source. Acknowledging the user's request without naming the source does not replace this notice.
Only an explicit choice of antislop during or after selects a session mode. A request to review, audit, or avoid file edits does not select a mode; read the global preference in that case. Another skill's mode does not select antislop's mode.
If the mode is unresolved, ask during/after and end the response; wait for the answer before any UI review, planning, or concept. For read-only tasks, put the active-mode notice only at the start of the final answer, never in progress messages. For editing tasks, announce before the first edit and omit it from the final answer.
To update antislop later: `npx antislop-ai --update`, or run `npx antislop-ai` and pick Overwrite them.
<!-- antislop:end -->
