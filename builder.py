#!/usr/bin/env python3
"""
NaniResumu Builder:
Compiles modular resume data + .env personal details into ATS-friendly OpenResume state JSON files.
"""

import os
import sys
import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" if (BASE_DIR / "data").exists() else BASE_DIR / "data.example"
BUILD_DIR = BASE_DIR / "build"
ENV_FILE = BASE_DIR / ".env"


def load_env(env_path: Path) -> dict:
    """Simple parser for .env file without external dependencies."""
    env_vars = {}
    if not env_path.exists():
        print(f"Warning: {env_path} not found. Using fallback or existing environment variables.", file=sys.stderr)
        return env_vars

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                env_vars[k] = v
    return env_vars


def load_json(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"Missing data file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_role_resume(role_key: str, env_vars: dict, master_data: dict) -> dict:
    roles = master_data["roles"]
    if role_key not in roles:
        raise ValueError(f"Role '{role_key}' not found in roles.json. Available: {list(roles.keys())}")

    role_cfg = roles[role_key]

    # 1. Profile from .env and role summary
    summary_key = role_cfg.get("summary_key", role_key)
    summary = master_data["profile"]["summaries"].get(
        summary_key,
        master_data["profile"]["summaries"].get("sqa", "")
    )

    profile = {
        "name": env_vars.get("RESUME_NAME", os.getenv("RESUME_NAME", "Your Name")),
        "email": env_vars.get("RESUME_EMAIL", os.getenv("RESUME_EMAIL", "your.email@example.com")),
        "phone": env_vars.get("RESUME_PHONE", os.getenv("RESUME_PHONE", "+1 XXX XXXX")),
        "location": env_vars.get("RESUME_LOCATION", os.getenv("RESUME_LOCATION", "City, Country")),
        "url": env_vars.get("RESUME_URL", os.getenv("RESUME_URL", "https://example.com")),
        "summary": summary
    }

    # 2. Educations
    target_edu_ids = role_cfg.get("educations", ["smiu_bsse"])
    edu_map = {e["id"]: e for e in master_data["education"]}
    educations = []
    for eid in target_edu_ids:
        if eid in edu_map:
            item = edu_map[eid].copy()
            # Clean internal fields for OpenResume
            item.pop("id", None)
            educations.append({
                "school": item.get("school", ""),
                "degree": item.get("degree", ""),
                "date": item.get("date", ""),
                "gpa": item.get("gpa", ""),
                "descriptions": item.get("descriptions", [])
            })

    # 3. Work Experiences
    target_work_ids = role_cfg.get("work_experiences", [])
    work_map = {w["id"]: w for w in master_data["work_experience"]}
    work_experiences = []
    for wid in target_work_ids:
        if wid in work_map:
            w_orig = work_map[wid]
            # Check for role-specific bullet points
            role_descs = w_orig.get("role_descriptions", {})
            descs = role_descs.get(role_key, w_orig.get("descriptions", []))
            work_experiences.append({
                "company": w_orig.get("company", ""),
                "jobTitle": w_orig.get("jobTitle", ""),
                "date": w_orig.get("date", ""),
                "descriptions": descs
            })

    # 4. Projects
    target_project_ids = role_cfg.get("projects", [])
    proj_map = {p["id"]: p for p in master_data["projects"]}
    projects = []
    for pid in target_project_ids:
        if pid in proj_map:
            p_orig = proj_map[pid]
            # Project name variant if defined
            p_name = p_orig.get("project_variants", {}).get(role_key, p_orig.get("project", ""))
            # Role-specific descriptions
            role_descs = p_orig.get("role_descriptions", {})
            descs = role_descs.get(role_key, p_orig.get("descriptions", []))
            projects.append({
                "project": p_name,
                "date": p_orig.get("date", ""),
                "descriptions": descs
            })

    # 5. Skills
    skills_key = role_cfg.get("skills_key", role_key)
    skills_descs = master_data["skills"]["role_skills"].get(
        skills_key,
        master_data["skills"]["role_skills"].get("sqa", [])
    )
    # Featured skill rating dots are optional and take up vertical space.
    # Default to empty unless role explicitly enables them via show_featured_skills: true
    show_featured = role_cfg.get("show_featured_skills", False)
    featured_skills_key = role_cfg.get("featured_skills_key", role_key)
    if show_featured and featured_skills_key:
        featured_skills = master_data["skills"]["featured_skills"].get(
            featured_skills_key, [{"skill": "", "rating": 4} for _ in range(6)]
        )
    else:
        featured_skills = [{"skill": "", "rating": 4} for _ in range(6)]

    skills = {
        "featuredSkills": featured_skills,
        "descriptions": skills_descs
    }

    # 6. Custom Section (Certifications)
    custom_descs = master_data.get("certifications", [])
    custom = {
        "descriptions": custom_descs
    }

    # 7. Redux Settings
    settings = role_cfg.get("settings", {
        "themeColor": "#38bdf8",
        "fontFamily": "Roboto",
        "fontSize": "11",
        "documentSize": "A4",
        "formToShow": {
            "workExperiences": bool(work_experiences),
            "educations": True,
            "projects": True,
            "skills": True,
            "custom": True
        },
        "formToHeading": {
            "workExperiences": "WORK EXPERIENCE",
            "educations": "EDUCATION",
            "projects": "RELEVANT PROJECTS",
            "skills": "SKILLS",
            "custom": "CERTIFICATIONS"
        },
        "formsOrder": ["workExperiences", "skills", "projects", "educations", "custom"],
        "showBulletPoints": {
            "educations": False,
            "projects": True,
            "skills": True,
            "custom": True
        }
    })

    # Compile the final OpenResume redux state tree
    open_resume_state = {
        "resume": {
            "profile": profile,
            "workExperiences": work_experiences,
            "educations": educations,
            "projects": projects,
            "skills": skills,
            "custom": custom
        },
        "settings": settings
    }

    return open_resume_state


def copy_to_clipboard(text: str) -> bool:
    """Copies text to system clipboard across Wayland, X11, macOS, and Windows."""
    import shutil
    import subprocess

    candidates = []

    # Prioritize based on active display environment
    if os.getenv("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
        candidates.append(["wl-copy"])

    if os.getenv("DISPLAY"):
        if shutil.which("xclip"):
            candidates.append(["xclip", "-selection", "clipboard"])
        if shutil.which("xsel"):
            candidates.append(["xsel", "--clipboard", "--input"])

    # General Linux fallbacks
    for tool_cmd in [
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"]
    ]:
        if shutil.which(tool_cmd[0]) and tool_cmd not in candidates:
            candidates.append(tool_cmd)

    # macOS and Windows / WSL fallbacks
    if shutil.which("pbcopy"):
        candidates.append(["pbcopy"])
    if shutil.which("clip.exe"):
        candidates.append(["clip.exe"])

    for cmd in candidates:
        try:
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3
            )
            if proc.returncode == 0:
                print(f"Copied JSON to clipboard via {cmd[0]}.")
                return True
        except Exception:
            continue

    print("Could not copy to clipboard (no responsive clipboard tool or active display server found). Output is saved in build/.", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description="NaniResumu Builder for OpenResume")
    parser.add_argument("--role", "-r", type=str, help="Specific role to build (e.g. sqa, devops, web_dev)")
    parser.add_argument("--all", "-a", action="store_true", help="Build all roles defined in roles.json")
    parser.add_argument("--list", "-l", action="store_true", help="List all available roles")
    parser.add_argument("--print", "-p", action="store_true", help="Print generated JSON to stdout")
    parser.add_argument("--copy", "-c", action="store_true", help="Copy generated JSON to clipboard")
    args = parser.parse_args()

    # Load master data
    master_data = {
        "profile": load_json(DATA_DIR / "profile.json"),
        "education": load_json(DATA_DIR / "education.json"),
        "work_experience": load_json(DATA_DIR / "work_experience.json"),
        "skills": load_json(DATA_DIR / "skills.json"),
        "projects": load_json(DATA_DIR / "projects.json"),
        "certifications": load_json(DATA_DIR / "certifications.json"),
        "roles": load_json(DATA_DIR / "roles.json")
    }

    if args.list:
        print("\nAvailable Resume Roles:")
        for rk, rval in master_data["roles"].items():
            print(f"  • {rk.ljust(15)} : {rval.get('name', rk)}")
        print()
        return

    env_vars = load_env(ENV_FILE)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    roles_to_build = []
    if args.all:
        roles_to_build = list(master_data["roles"].keys())
    elif args.role:
        roles_to_build = [args.role]
    else:
        # Default to sqa if nothing specified
        print("No role specified. Defaulting to 'sqa'. Use --all to build all.")
        roles_to_build = ["sqa"]

    last_json_str = ""
    for rk in roles_to_build:
        try:
            state = build_role_resume(rk, env_vars, master_data)
            out_file = BUILD_DIR / f"{rk}.json"
            json_str = json.dumps(state, indent=2, ensure_ascii=False)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(json_str)

            print(f"Built '{rk}' -> {out_file} ({len(state['resume']['projects'])} projects, {len(state['resume']['workExperiences'])} jobs)")
            last_json_str = json_str
        except Exception as e:
            print(f"Error building role '{rk}': {e}", file=sys.stderr)

    if args.print and last_json_str:
        print("\n" + last_json_str)

    if args.copy and last_json_str:
        copy_to_clipboard(last_json_str)


if __name__ == "__main__":
    main()
