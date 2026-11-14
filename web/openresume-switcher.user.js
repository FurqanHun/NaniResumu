// ==UserScript==
// @name         OpenResume Profile Switcher
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Switch effortlessly between different ATS-friendly resumes on open-resume.com without container tabs!
// @author       FurqanHun
// @match        https://www.open-resume.com/resume-builder*
// @match        http://localhost:3000/resume-builder*
// @downloadURL  https://raw.githubusercontent.com/FurqanHun/naniresumu/master/web/openresume-switcher.user.js
// @updateURL    https://raw.githubusercontent.com/FurqanHun/naniresumu/master/web/openresume-switcher.user.js
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// ==/UserScript==

(function () {
    'use strict';

    const LOCAL_SERVER = "http://127.0.0.1:4040";

    function createUI(resumes) {
        if (document.getElementById("openresume-switcher-bar")) {
            document.getElementById("openresume-switcher-bar").remove();
        }

        const bar = document.createElement("div");
        bar.id = "openresume-switcher-bar";
        bar.style.position = "fixed";
        bar.style.top = "12px";
        bar.style.right = "180px";
        bar.style.zIndex = "99999";
        bar.style.display = "flex";
        bar.style.alignItems = "center";
        bar.style.gap = "8px";
        bar.style.background = "#1e293b";
        bar.style.color = "#f8fafc";
        bar.style.padding = "6px 12px";
        bar.style.borderRadius = "24px";
        bar.style.boxShadow = "0 4px 14px rgba(0,0,0,0.25)";
        bar.style.fontSize = "13px";
        bar.style.fontFamily = "system-ui, -apple-system, sans-serif";
        bar.style.border = "1px solid #334155";

        const label = document.createElement("span");
        label.innerHTML = "<b>Profile:</b>";
        bar.appendChild(label);

        const select = document.createElement("select");
        select.style.background = "#0f172a";
        select.style.color = "#38bdf8";
        select.style.border = "1px solid #475569";
        select.style.padding = "4px 8px";
        select.style.borderRadius = "6px";
        select.style.fontWeight = "600";
        select.style.cursor = "pointer";
        select.setAttribute("aria-label", "Select Resume Profile");

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Select Resume";
        select.appendChild(defaultOption);

        resumes.forEach(r => {
            const opt = document.createElement("option");
            opt.value = r.id;
            opt.textContent = `${r.name} (${r.id})`;
            select.appendChild(opt);
        });

        select.addEventListener("change", function () {
            const roleId = select.value;
            if (!roleId) return;
            loadResume(roleId);
        });

        bar.appendChild(select);

        // Sync / Refresh button
        const refreshBtn = document.createElement("button");
        refreshBtn.innerHTML = "Sync";
        refreshBtn.title = "Reload resumes from local server";
        refreshBtn.style.background = "#334155";
        refreshBtn.style.border = "none";
        refreshBtn.style.color = "#cbd5e1";
        refreshBtn.style.padding = "4px 8px";
        refreshBtn.style.borderRadius = "6px";
        refreshBtn.style.cursor = "pointer";
        refreshBtn.setAttribute("aria-label", "Sync Resumes");
        refreshBtn.onclick = () => fetchResumes();
        bar.appendChild(refreshBtn);

        // Manual Paste button (fallback if local server isn't running)
        const pasteBtn = document.createElement("button");
        pasteBtn.innerHTML = "Paste JSON";
        pasteBtn.title = "Manually paste an open-resume-state JSON";
        pasteBtn.style.background = "#334155";
        pasteBtn.style.border = "none";
        pasteBtn.style.color = "#cbd5e1";
        pasteBtn.style.padding = "4px 8px";
        pasteBtn.style.borderRadius = "6px";
        pasteBtn.style.cursor = "pointer";
        pasteBtn.setAttribute("aria-label", "Paste JSON Manually");
        pasteBtn.onclick = () => {
            const raw = prompt("Paste your OpenResume state JSON here:");
            if (raw) {
                try {
                    const parsed = JSON.parse(raw);
                    localStorage.setItem("open-resume-state", JSON.stringify(parsed));
                    window.location.reload();
                } catch (e) {
                    alert("Invalid JSON: " + e.message);
                }
            }
        };
        bar.appendChild(pasteBtn);

        document.body.appendChild(bar);
    }

    function loadResume(roleId) {
        console.log(`[OpenResume Switcher] Loading resume for role '${roleId}'...`);
        const url = `${LOCAL_SERVER}/api/resume?role=${roleId}`;

        const req = (typeof GM_xmlhttpRequest !== "undefined") ? GM_xmlhttpRequest : window.fetch;

        if (typeof GM_xmlhttpRequest !== "undefined") {
            GM_xmlhttpRequest({
                method: "GET",
                url: url,
                onload: function (response) {
                    if (response.status >= 200 && response.status < 300) {
                        try {
                            const data = JSON.parse(response.responseText);
                            localStorage.setItem("open-resume-state", JSON.stringify(data));
                            console.log("[OpenResume Switcher] Resume state saved to localStorage. Reloading...");
                            window.location.reload();
                        } catch (e) {
                            alert("Failed to parse response JSON: " + e.message);
                        }
                    } else {
                        alert(`Server returned error ${response.status}: ${response.statusText}`);
                    }
                },
                onerror: function (err) {
                    alert("Could not connect to NaniResumu local server at " + LOCAL_SERVER + ". Please make sure `python server.py` is running!");
                }
            });
        } else {
            fetch(url)
                .then(res => res.json())
                .then(data => {
                    localStorage.setItem("open-resume-state", JSON.stringify(data));
                    window.location.reload();
                })
                .catch(err => {
                    alert("Could not connect to NaniResumu server: " + err.message);
                });
        }
    }

    function fetchResumes() {
        const url = `${LOCAL_SERVER}/api/resumes`;
        const fallbackResumes = [
            { id: "sqa", name: "SQA Trainee" },
            { id: "devops", name: "DevOps Trainee / Engineer" },
            { id: "web_dev", name: "Web / Mobile Developer" },
            { id: "cybersecurity", name: "Cybersecurity Intern" },
            { id: "it_officer", name: "IT Officer / Systems & Network" },
            { id: "ml_python", name: "Python & NLP / Data Developer" },
            { id: "game_dev", name: "Game Developer / Unity & C#" }
        ];

        if (typeof GM_xmlhttpRequest !== "undefined") {
            GM_xmlhttpRequest({
                method: "GET",
                url: url,
                onload: function (response) {
                    if (response.status === 200) {
                        try {
                            const list = JSON.parse(response.responseText);
                            createUI(list);
                        } catch (e) {
                            createUI(fallbackResumes);
                        }
                    } else {
                        createUI(fallbackResumes);
                    }
                },
                onerror: function () {
                    createUI(fallbackResumes);
                }
            });
        } else {
            fetch(url)
                .then(r => r.json())
                .then(list => createUI(list))
                .catch(() => createUI(fallbackResumes));
        }
    }

    // Wait for DOM to be ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", fetchResumes);
    } else {
        fetchResumes();
    }
})();
