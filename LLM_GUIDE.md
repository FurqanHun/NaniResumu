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
2. Select the 4 or 5 most relevant projects from `data/projects.json` matching the stack.
3. In `data/profile.json`, add a concise 2-3 sentence summary tailored to this position.
4. In `data/skills.json`, verify that relevant skills match the posting keywords.
5. In `data/roles.json`, define a new role preset using `"documentSize": "A4"` and the standard section order.
6. Run `python3 builder.py --role <new_role_id>` to compile the Redux state.
7. Report the selected projects and role ID so I can switch to it on OpenResume.
```

---

## What the AI assistant handles automatically

When following `AGENTS.md`, the AI assistant enforces these standards:

1. **Privacy preservation**:
   - The assistant never inspects or reads `.env` or `build/` files directly.
   - Contact details are injected by `builder.py` at build time.
2. **ATS single-page compliance**:
   - Caps project selection at 4 to 5 projects per resume.
   - Limits bullets to 1 or 2 concise lines per project.
   - Uses active past-tense verbs and avoids first-person pronouns.
   - Leaves `featuredSkills` rating circles empty by default to prevent vertical page overflow.
3. **Harmonized section order and page sizing**:
   - Enforces A4 page sizing (`"documentSize": "A4"`).
   - Keeps section order consistent: `workExperiences` -> `skills` -> `projects` -> `educations` -> `custom`.
