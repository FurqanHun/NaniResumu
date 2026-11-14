# NaniResumu (何レジュメ)

Modular resume compiler and switcher for OpenResume.

---

## The problem

[OpenResume](https://www.open-resume.com/resume-builder) generates single-page, ATS-compliant resumes, but stores only one active resume state in browser `localStorage`. Managing multiple role-tailored resumes (such as SQA, DevOps, Web Development, or Systems) typically requires keeping multiple browser profiles, separate container tabs, or manually copy-pasting contact details and project bullets across tabs.

NaniResumu decouples contact details and resume content into modular files:
1. **Contact details in `.env`**: Name, email, phone, location, and URLs live in a single environment file.
2. **Modular resume sections in `data/`**: Projects, skills, education, and work experience live in structured JSON files.
3. **OpenResume Redux compiler (`builder.py`)**: Merges contact details and selected role data into valid OpenResume state JSON files.
4. **Browser integration**: Switch profiles in OpenResume via a userscript dropdown, bookmarklet, or local dashboard.
5. **Private data isolation**: Personal data in `.env` and `data/` is excluded from git tracking via `.gitignore`. Anonymized schemas live in `data.example/` for public repository sharing.

---

## Requirements

- **Python**: Version 3.8 or later. Uses only standard library modules (`json`, `http.server`, `urllib`, `argparse`, `pathlib`). No `pip install` required.
- **Web browser**: Any modern browser (Firefox, Librewolf, Chrome, Brave, Chromium, Edge).
- **Browser extension (optional)**: [Tampermonkey](https://www.tampermonkey.net/) or [Violentmonkey](https://violentmonkey.github.io/) for 1-click in-page resume switching.
- **System clipboard tools (optional)**: When using the `--copy` flag, `builder.py` automatically detects and uses whichever clipboard tool is available: `wl-copy` (Wayland), `xsel` or `xclip` (X11), `pbcopy` (macOS), or `clip.exe` (Windows/WSL).

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/FurqanHun/naniresumu.git
cd naniresumu
```

### 2. Configure environment variables
Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` with your personal contact details:
```bash
RESUME_NAME="Your Full Name"
RESUME_EMAIL="your.email@example.com"
RESUME_PHONE="+1 XXX XXXX"
RESUME_LOCATION="City, Country"
RESUME_URL="https://yourwebsite.com"
```
`.env` is ignored by git to prevent committing personal contact information.

### 3. Initialize resume data
If starting with your own data, copy the template schema directory:
```bash
cp -r data.example data
```
`data/` is ignored by git so your work experience, education records, and projects remain private. If `data/` is omitted, `builder.py` and `server.py` fall back to `data.example/` automatically.

Customize the JSON files inside `data/`:
- `data/profile.json`: Professional summaries keyed by role.
- `data/education.json`: Degrees, institutions, dates, and GPAs.
- `data/work_experience.json`: Job titles, companies, dates, and bullet variants.
- `data/skills.json`: Categorized technical skill strings.
- `data/projects.json`: Project catalog with links, dates, and role-tailored bullets.
- `data/certifications.json`: Certifications and test percentiles.
- `data/roles.json`: Presets that choose which items from each section to assemble into a resume.

### 4. Build resumes
Compile all presets defined in `roles.json`:
```bash
python3 builder.py --all
```
Compiled OpenResume Redux state files are written to `build/<role>.json`.

---

## Command line usage

Build a single role preset:
```bash
python3 builder.py --role software_engineer
```

Build and copy the JSON state directly to your system clipboard:
```bash
python3 builder.py --role software_engineer --copy
```

Print the generated JSON state to standard output:
```bash
python3 builder.py --role software_engineer --print
```

List all available role presets:
```bash
python3 builder.py --list
```

---

## Switching resumes in OpenResume

Start the local server:
```bash
python3 server.py
```
The server runs on `http://127.0.0.1:4040` with CORS enabled.

### Method A: Userscript dropdown (Recommended)
1. Install [Tampermonkey](https://www.tampermonkey.net/) or [Violentmonkey](https://violentmonkey.github.io/) in your browser.
2. Install the userscript directly:
   - **Direct install (1 click)**: Open [openresume-switcher.user.js](https://raw.githubusercontent.com/FurqanHun/naniresumu/main/web/openresume-switcher.user.js) in your browser (Tampermonkey will automatically prompt to install).
   - **Or via local server**: Open `http://127.0.0.1:4040/openresume-switcher.user.js` while `server.py` is running.
3. Navigate to [https://www.open-resume.com/resume-builder](https://www.open-resume.com/resume-builder).
4. A dropdown menu appears in the top navigation bar. Select any role to load that resume state into OpenResume immediately.

### Method B: Browser bookmarklet
1. Create a new bookmark in your browser named `OpenResume Switcher`.
2. Copy the one-line code from [`web/bookmarklet.js`](web/bookmarklet.js) into the URL field.
3. Click the bookmark anytime you are on [https://www.open-resume.com/resume-builder](https://www.open-resume.com/resume-builder) to open a popup selector.

### Method C: Local web dashboard
Visit `http://127.0.0.1:4040` to view all configured roles, inspect card summaries, trigger rebuilds, copy JSON, or download individual state files.

---

## Maintaining and tailoring resumes with an AI agent

You can use an AI coding assistant (Antigravity, Claude, ChatGPT, Cursor, or Gemini) to populate your initial data, log new projects, or generate tailored resumes for specific job descriptions.

See [LLM_GUIDE.md](LLM_GUIDE.md) for ready-to-copy prompts covering:
1. **Initial data population**: Importing experience from existing resume text, LinkedIn profiles, or project lists.
2. **Project catalog maintenance**: Adding new repositories and tagging role-tailored bullet variants.
3. **Job-targeted tailoring**: Automatically matching keywords, drafting summaries, and generating single-page A4 presets.

All architectural constraints, ATS standards, and privacy rules for AI agents are defined in [AGENTS.md](AGENTS.md).

---

## OpenResume compatibility and self-hosting

NaniResumu compiles into the Redux state schema of [OpenResume](https://www.open-resume.com/resume-builder), an open-source project created by [Xitang Zhao](https://github.com/xitanggg/open-resume).

Key architectural notes:
- **Frozen schema stability**: Upstream development on OpenResume has remained stable and dormant since late 2024. Because no breaking changes are introduced to the Redux state structure or browser localStorage keys, compiled presets remain compatible over time.
- **Local self-hosting**: OpenResume is an open-source Next.js application with no backend dependencies. If `open-resume.com` is ever unavailable, you can clone and run it locally:
  ```bash
  git clone https://github.com/xitanggg/open-resume.git
  cd open-resume
  npm install
  npm run dev
  ```
  The included userscript ([web/openresume-switcher.user.js](web/openresume-switcher.user.js)) already matches both `https://www.open-resume.com/resume-builder*` and `http://localhost:3000/resume-builder*`.
- **Zero vendor lock-in**: Your master data is maintained in clean JSON files inside `data/`. If you ever switch to another resume renderer (such as jsonresume, Typst, LaTeX, or a custom HTML template), your project catalog, experience bullets, and skills remain portable and independent. Maybe in future the builder would allow export to multiple formats.

---

## Repository layout

```
naniresumu/
├── .env                      # Personal contact details (ignored in git)
├── .env.example              # Environment variable template
├── builder.py                # Python compiler: merges .env + data/ -> build/*.json
├── server.py                 # Local CORS HTTP server (port 4040)
├── AGENTS.md                 # Architecture rules for AI coding assistants
├── LLM_GUIDE.md              # Prompt guide for tailoring resumes to job postings
├── README.md                 # Project documentation
├── data.example/             # Anonymized sample schemas (tracked in git)
│   ├── profile.json          # Role-specific summary templates
│   ├── education.json        # Academic degree schema
│   ├── work_experience.json  # Employment and bullet schema
│   ├── skills.json           # Categorized skill lists
│   ├── projects.json         # Project catalog schema
│   ├── certifications.json   # Certifications list
│   └── roles.json            # Role composition presets
├── data/                     # Private master database (ignored in git)
├── build/                    # Compiled OpenResume JSON states (ignored in git)
└── web/
    ├── index.html            # Local web dashboard
    ├── openresume-switcher.user.js # Tampermonkey userscript for open-resume.com
    └── bookmarklet.js        # Drag-and-drop browser bookmarklet
```

---

## Acknowledgments

This project was sloppified and structured with Antigravity (Gemini 3.8 Flash) and somewhat de-sloppified using antislop skill suite.
