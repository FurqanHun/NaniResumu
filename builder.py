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

PAGE_1_CAPACITY_PT = 792.0  # Usable content height on standard A4 page (842pt - margins/top bar)


def estimate_resume_height(role_key: str, role_cfg: dict, master_data: dict, font_size_override: str = None) -> tuple:
    """
    Estimates the vertical point height and section boundary positions
    based on OpenResume's React-PDF spacing metrics.
    Returns: (total_height, section_positions, straddle_section, orphan_warning)
    """
    settings = role_cfg.get("settings", {})
    raw_fs = font_size_override if font_size_override else settings.get("fontSize", "11")
    try:
        font_size = float(raw_fs)
    except ValueError:
        font_size = 11.0

    scale = font_size / 11.0
    line_h = 13.0 * scale
    heading_h = 35.0 * scale

    # 1. Top accent bar and profile section
    h = 10.5  # Top accent bar height
    h += 12.0  # Profile container margin top
    h += 24.0  # Name heading

    summary_key = role_cfg.get("summary_key", role_key)
    summary = master_data.get("profile", {}).get("summaries", {}).get(summary_key, "")
    if summary:
        # Approximate lines based on ~85 characters per line at standard width
        lines = max(1, len(summary) // 85 + 1)
        h += lines * line_h + 4.0

    # Contact details row (email, phone, location, links)
    h += line_h + 6.0

    # 2. Form sections in configured order
    order = settings.get("formsOrder", ["workExperiences", "skills", "projects", "educations", "custom"])
    form_to_show = settings.get("formToShow", {})

    section_positions = {}
    for section in order:
        if not form_to_show.get(section, True):
            continue

        sec_start = h

        if section == "workExperiences":
            work_ids = role_cfg.get("work_experiences", [])
            if not work_ids:
                continue
            h += heading_h
            for wid in work_ids:
                h += 16.0 * scale  # Company and title row
                w_item = next((w for w in master_data.get("work_experience", []) if w["id"] == wid), None)
                if w_item:
                    descs = w_item.get("role_descriptions", {}).get(role_key, w_item.get("descriptions", []))
                    for d in descs:
                        lines = max(1, len(d) // 85 + 1)
                        h += lines * line_h + 2.0
                h += 6.0

        elif section == "skills":
            skills_key = role_cfg.get("skills_key", role_key)
            descs = master_data.get("skills", {}).get("role_skills", {}).get(skills_key, [])
            if not descs:
                continue
            h += heading_h
            for d in descs:
                lines = max(1, len(d) // 85 + 1)
                h += lines * line_h + 2.0
            h += 6.0

        elif section == "projects":
            proj_ids = role_cfg.get("projects", [])
            if not proj_ids:
                continue
            h += heading_h
            for pid in proj_ids:
                h += 16.0 * scale  # Project title and date row
                p_item = next((p for p in master_data.get("projects", []) if p["id"] == pid), None)
                if p_item:
                    descs = p_item.get("role_descriptions", {}).get(role_key, p_item.get("descriptions", []))
                    for d in descs:
                        lines = max(1, len(d) // 85 + 1)
                        h += lines * line_h + 2.0
                h += 6.0

        elif section == "educations":
            edu_ids = role_cfg.get("educations", [])
            if not edu_ids:
                continue
            h += heading_h
            show_bullets = settings.get("showBulletPoints", {}).get("educations", False)
            for eid in edu_ids:
                h += 24.0 * scale  # School and degree row
                e_item = next((e for e in master_data.get("education", []) if e["id"] == eid), None)
                if e_item and show_bullets:
                    for d in e_item.get("descriptions", []):
                        lines = max(1, len(d) // 85 + 1)
                        h += lines * line_h + 2.0
                h += 4.0

        elif section == "custom":
            descs = master_data.get("certifications", [])
            if not descs:
                continue
            h += heading_h
            for d in descs:
                lines = max(1, len(d) // 85 + 1)
                h += lines * line_h + 2.0
            h += 4.0

        section_positions[section] = (sec_start, h)

    # 3. Detect straddles and orphan heading risks across the page 1 cutoff
    straddle_section = None
    orphan_warning = None
    for sec_name, (s_start, s_end) in section_positions.items():
        if s_start < PAGE_1_CAPACITY_PT < s_end:
            straddle_section = sec_name
            # If the heading itself fits on page 1 (starts within 55pt of cutoff),
            # but the content spills onto page 2, it is a high-risk orphan heading.
            if (PAGE_1_CAPACITY_PT - s_start) <= 55.0:
                heading_label = settings.get("formToHeading", {}).get(sec_name, sec_name.upper())
                orphan_warning = (
                    f"Section '{heading_label}' starts at {s_start:.0f}pt (within 55pt of Page 1 cutoff). "
                    f"In OpenResume, the section heading will remain on Page 1 while bullets spill onto Page 2 "
                    f"with zero top margin."
                )
            break

    return h, section_positions, straddle_section, orphan_warning


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


def build_role_resume(role_key: str, env_vars: dict, master_data: dict, auto_fit: bool = False) -> tuple:
    roles = master_data["roles"]
    if role_key not in roles:
        raise ValueError(f"Role '{role_key}' not found in roles.json. Available: {list(roles.keys())}")

    role_cfg = roles[role_key]
    role_settings = dict(role_cfg.get("settings", {}))

    # Auto-fit evaluation: if enabled, check if font 10 avoids accidental 1-page overflow
    should_auto_fit = auto_fit or role_cfg.get("auto_fit", False) or role_settings.get("auto_fit", False)

    applied_auto_fit = False
    if should_auto_fit:
        current_fs = str(role_settings.get("fontSize", "11"))
        est_h, _, _, _ = estimate_resume_height(role_key, role_cfg, master_data, font_size_override=current_fs)
        if est_h > PAGE_1_CAPACITY_PT and current_fs != "10":
            est_h_10, _, _, _ = estimate_resume_height(role_key, role_cfg, master_data, font_size_override="10")
            if est_h_10 <= PAGE_1_CAPACITY_PT + 15.0:
                role_settings["fontSize"] = "10"
                applied_auto_fit = True

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
    default_form_to_show = {
        "workExperiences": bool(work_experiences),
        "educations": bool(educations),
        "projects": bool(projects),
        "skills": bool(skills_descs),
        "custom": bool(custom_descs)
    }

    form_to_show = default_form_to_show.copy()
    if "formToShow" in role_settings:
        form_to_show.update(role_settings["formToShow"])
    if not work_experiences:
        form_to_show["workExperiences"] = False

    settings = {
        "themeColor": role_settings.get("themeColor", "#38bdf8"),
        "fontFamily": role_settings.get("fontFamily", "Roboto"),
        "fontSize": role_settings.get("fontSize", "11"),
        "documentSize": role_settings.get("documentSize", "A4"),
        "formToShow": form_to_show,
        "formToHeading": role_settings.get("formToHeading", {
            "workExperiences": "WORK EXPERIENCE",
            "educations": "EDUCATION",
            "projects": "RELEVANT PROJECTS",
            "skills": "SKILLS",
            "custom": "CERTIFICATIONS"
        }),
        "formsOrder": role_settings.get("formsOrder", [
            "workExperiences", "skills", "projects", "educations", "custom"
        ]),
        "showBulletPoints": role_settings.get("showBulletPoints", {
            "educations": False,
            "projects": True,
            "skills": True,
            "custom": True
        })
    }

    # Final layout metrics evaluation
    h, pos, straddle, orphan_warning = estimate_resume_height(
        role_key,
        {**role_cfg, "settings": settings},
        master_data
    )

    metrics = {
        "height_pt": round(h, 1),
        "straddle_section": straddle,
        "orphan_warning": orphan_warning,
        "applied_auto_fit": applied_auto_fit,
        "font_size": settings["fontSize"],
        "num_projects": len(projects),
        "num_jobs": len(work_experiences)
    }

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

    return open_resume_state, metrics


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
    parser.add_argument("--check", action="store_true", help="Validate page budget and orphan risks across roles without building")
    parser.add_argument("--auto-fit", action="store_true", help="Automatically apply compact font size (10pt) to fit 1-page roles safely")
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

    if args.check:
        print("\n--- NaniResumu Layout Budget & Orphan Validator ---")
        print(f"{'Role':16} {'Target':8} {'Height':10} {'Fill %':8} {'Font':6} {'Status'}")
        print("-" * 72)
        for rk, rval in master_data["roles"].items():
            settings = rval.get("settings", {})
            h, _, straddle, orphan = estimate_resume_height(rk, rval, master_data)
            fill_pct = (h / PAGE_1_CAPACITY_PT) * 100

            if h <= PAGE_1_CAPACITY_PT:
                status = "OK (Fits 1 page)"
            else:
                spill = h - PAGE_1_CAPACITY_PT
                status = f"OVERFLOW (+{spill:.0f}pt onto Page 2)"

            print(f"{rk:16} {'1p':8} {h:6.1f}pt   {fill_pct:5.1f}%   {settings.get('fontSize', '11'):4}   {status}")
            if orphan:
                print(f"   ⚠️  ORPHAN RISK: {orphan}")
            elif straddle:
                print(f"   ℹ️  Note: Section '{straddle}' spans page boundary.")
        print("-" * 72 + "\n")
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
            state, metrics = build_role_resume(rk, env_vars, master_data, auto_fit=args.auto_fit)
            out_file = BUILD_DIR / f"{rk}.json"
            json_str = json.dumps(state, indent=2, ensure_ascii=False)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(json_str)

            # Build status reporting
            h = metrics["height_pt"]
            fill_pct = (h / PAGE_1_CAPACITY_PT) * 100
            fs = metrics["font_size"]
            fit_note = " [auto-fit font 10 applied]" if metrics["applied_auto_fit"] else ""

            if h <= PAGE_1_CAPACITY_PT:
                print(f"Built '{rk}' -> {out_file} [1 Page: {h:.0f}pt / {PAGE_1_CAPACITY_PT:.0f}pt ({fill_pct:.0f}% full, font {fs}){fit_note}]")
            else:
                spill = h - PAGE_1_CAPACITY_PT
                print(f"Built '{rk}' -> {out_file} [OVERFLOW: {h:.0f}pt / {PAGE_1_CAPACITY_PT:.0f}pt (+{spill:.0f}pt on Page 2, font {fs})]")
                print(f"  ⚠️  Accidental Page 2 Overflow: {spill:.0f}pt spills onto Page 2 in OpenResume.")
                if metrics["orphan_warning"]:
                    print(f"  ⚠️  Orphan Risk: {metrics['orphan_warning']}")
                print(f"  💡 Recommendations: Run with --auto-fit, drop fontSize to '10' in settings, or reduce projects from {metrics['num_projects']} to {metrics['num_projects'] - 1}.")

            last_json_str = json_str
        except Exception as e:
            print(f"Error building role '{rk}': {e}", file=sys.stderr)

    if args.print and last_json_str:
        print("\n" + last_json_str)

    if args.copy and last_json_str:
        copy_to_clipboard(last_json_str)


if __name__ == "__main__":
    main()
