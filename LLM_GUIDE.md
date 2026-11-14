# LLM Guide: Maintaining and Tailoring Resumes with AI

This guide explains how to use an LLM or AI coding assistant (Antigravity, Claude, ChatGPT, Cursor, Gemini, Deepseek, etc) to populate your data, keep projects updated, and tailor resumes for specific job descriptions.

All agent-specific rules, ATS formatting constraints, and privacy boundaries are codified in [AGENTS.md](AGENTS.md). Always instruct the AI assistant to consult `AGENTS.md` first.

---

## Workflow 1: Populating data from an existing resume or profile

If you are setting up NaniResumu for the first time with an existing resume (PDF text, LinkedIn export, or portfolio website), copy and paste this prompt:

```markdown
I have initialized NaniResumu at `/path/to/naniresumu`.

First, read `AGENTS.md` to understand the architecture, data schemas, and constraints.

Here is my current resume / background text:
---
[PASTE RESUME TEXT, LINKEDIN EXPORT, PROJECT LIST, PDF/DOC with personal data redacted or attach the URL (if the agent can access internet) HERE]
---

Please do the following:
1. Initialize my `data/` directory by referencing the schemas in `data.example/`.
2. Populate `data/profile.json` with professional summaries for my target roles.
3. Populate `data/education.json` with my degrees and dates (keep GPA in the gpa field, not in degree).
4. Populate `data/work_experience.json` with my employment history and action-oriented bullets.
5. Populate `data/skills.json` with categorized skill groups.
6. Populate `data/projects.json` with structured project entries, dates, links, and role-tailored bullets.
7. Populate `data/certifications.json` with my certifications.
8. Create initial presets in `data/roles.json`.
9. Run `python3 builder.py --all` to verify that all presets compile cleanly.
```

---

## Workflow 2: Adding a new project or work experience

When you complete a new project, release an open-source library, or update your job responsibilities:

```markdown
I have a new project to add to my NaniResumu catalog at `/path/to/naniresumu`.

First, read `AGENTS.md` for schema rules.

Project details:
- Title: [Project Name: Subtitle]
- Date: [Month Year - Month Year or Present]
- Link: [Repository or Demo URL]
- Technologies: [Tags / Stack]
- Core description: [1-2 sentences on problem solved, implementation, and metrics]
- Role perspectives: [e.g. SQA angle, DevOps angle, Frontend angle]

Please:
1. Add this entry to `data/projects.json`.
2. Add the project ID to any relevant role presets in `data/roles.json`.
3. Run `python3 builder.py --all` to verify that the build succeeds without overflowing single-page limits.
```

---

## Workflow 3: Tailoring a resume for a specific job posting

When applying for a specific position:

```markdown
I have my resume system at `/path/to/naniresumu`.

First, read `AGENTS.md` to review the single-page A4 constraints, section ordering, and privacy rules.

Here is the job description I am targeting:
---
[PASTE JOB DESCRIPTION HERE]
---

Please do the following:
1. Analyze the job posting for tech stack, core responsibilities, and seniority focus.
2. Select 4 or 5 projects from `data/projects.json` matching the stack.
3. In `data/profile.json`, add a concise 2-3 sentence summary tailored to this position.
4. In `data/skills.json`, verify that relevant skills match the posting keywords.
5. In `data/roles.json`, define a new role preset using `"documentSize": "A4"` and the standard section order.
6. Run `python3 builder.py --role <new_role_id> --auto-fit` to compile the Redux state and verify single-page fit.
7. Report the selected projects and role ID so I can switch to it on OpenResume.
```

---

## What the AI assistant handles automatically

When following `AGENTS.md`, the AI assistant enforces these standards:

1. **Privacy preservation**:
   - The assistant never inspects or reads `.env` or `build/` files directly.
   - Contact details are injected by `builder.py` at build time.
2. **Strict single-page ATS compliance**:
   - Strictly enforces an impact-focused single A4 page (~792pt budget).
   - Rejects artificial multi-page string hacks (`\n\n`) that corrupt ATS text parsing.
   - Uses active past-tense verbs and avoids first-person pronouns.
   - Leaves `featuredSkills` rating circles empty by default to prevent vertical page overflow.
3. **No guessing or hallucination of missing data**:
   - Never fabricates dates, job responsibilities, project descriptions, or credentials.
   - Asks the user directly whenever career dates, tenure, or project details are missing from provided notes.
4. **Settings defaults and typography guardrails**:
   - Enforces proven defaults (A4 size, Roboto font, 11pt standard size, #38bdf8 theme color, empty featuredSkills).
   - Never changes styling unless explicitly instructed by the user.
   - Enforces typography safety: limits font sizes to 10-12pt and restricts fonts to OpenResume's 10 supported families to prevent text from overflowing or breaking ATS scanners.
5. **Harmonized section order and headings**:
   - Enforces A4 page sizing (`"documentSize": "A4"`).
   - Keeps section order consistent: `workExperiences` -> `skills` -> `projects` -> `educations` -> `custom`.
6. **Additive catalog safety**:
   - Treats `data/*.json` as an additive master repository.
   - Appends new role presets and projects without overwriting or truncating existing catalog entries.
7. **ATS bullet phrasing and metrics**:
   - Strictly enforces `antislop-copywriting` standards (eliminates AI buzzwords like *leveraged* or *spearheaded*, rejects significance inflation).
   - Starts bullets with strong action verbs (*Engineered*, *Architected*, *Containerized*).
   - Enforces zero first-person pronouns and concise 1-2 line density.
8. **Link and identifier integrity**:
   - Enforces lowercase `snake_case` IDs across all JSON catalogs.
   - Sets `"link": ""` when URLs are unavailable instead of generating placeholder or fake domains.
