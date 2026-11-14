// ==UserScript==
// @name         OpenResume Profile Switcher
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Fast profile switcher for NaniResumu on open-resume.com
// @author       FurqanHun
// @match        https://www.open-resume.com/resume-builder*
// @match        http://localhost:3000/resume-builder*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// ==/UserScript==

(function () {
    'use strict';

    const LOCAL_SERVER = "http://127.0.0.1:4040";

    // Allow scrolling inside the preview iframe
    function enableIframeScroll() {
        document.querySelectorAll("iframe").forEach(iframe => {
            try {
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                if (doc && doc.body && doc.body.style.overflow === "hidden") {
                    doc.body.style.setProperty("overflow", "auto", "important");
                }
            } catch (e) { }
        });
    }

    setInterval(enableIframeScroll, 1500);

    // Floating Switcher Toolbar
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
        bar.style.border = "1px solid #334155";
        bar.style.fontFamily = "system-ui, -apple-system, sans-serif";
        bar.style.fontSize = "13px";

        bar.innerHTML = `
            <span style="font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 4px;">
                ⚡ NaniResumu
            </span>
            <select id="nr-role-select" style="background: #0f172a; color: #f8fafc; border: 1px solid #475569; padding: 4px 8px; border-radius: 6px; font-size: 12px; outline: none; cursor: pointer;">
                <option value="" disabled selected>Select Role Preset...</option>
                ${resumes.map(r => `<option value="${r.id}">${r.name} (${r.id})</option>`).join("")}
            </select>
            <button id="nr-paste-btn" title="Paste JSON manually" style="background: #334155; color: #e2e8f0; border: none; padding: 4px 8px; border-radius: 6px; font-size: 11px; cursor: pointer;">
                📋 Paste
            </button>
        `;

        document.body.appendChild(bar);

        const select = document.getElementById("nr-role-select");
        select.addEventListener("change", (e) => {
            const roleId = e.target.value;
            if (!roleId) return;

            select.disabled = true;
            loadRoleFromBackend(roleId, () => {
                select.disabled = false;
            });
        });

        document.getElementById("nr-paste-btn").addEventListener("click", () => {
            const text = prompt("Paste your compiled OpenResume JSON here:");
            if (text) {
                try {
                    const parsed = JSON.parse(text);
                    localStorage.setItem("open-resume-state", JSON.stringify(parsed));
                    location.reload();
                } catch (err) {
                    alert("Invalid JSON format: " + err.message);
                }
            }
        });
    }

    function loadRoleFromBackend(roleId, onDone) {
        if (typeof GM_xmlhttpRequest !== "undefined") {
            GM_xmlhttpRequest({
                method: "GET",
                url: `${LOCAL_SERVER}/api/resume?role=${roleId}`,
                onload: function (response) {
                    try {
                        const data = JSON.parse(response.responseText);
                        localStorage.setItem("open-resume-state", JSON.stringify(data));
                        location.reload();
                    } catch (e) {
                        alert("Error parsing resume JSON: " + e.message);
                        if (onDone) onDone();
                    }
                },
                onerror: function () {
                    alert("Could not reach local server at " + LOCAL_SERVER + ". Is server.py running?");
                    if (onDone) onDone();
                }
            });
        } else {
            fetch(`${LOCAL_SERVER}/api/resume?role=${roleId}`)
                .then(r => r.json())
                .then(data => {
                    localStorage.setItem("open-resume-state", JSON.stringify(data));
                    location.reload();
                })
                .catch(err => {
                    alert("Could not reach local server: " + err.message);
                    if (onDone) onDone();
                });
        }
    }

    function fetchRoles() {
        const fallbackRoles = [
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
                url: `${LOCAL_SERVER}/api/resumes`,
                onload: function (res) {
                    try {
                        createUI(JSON.parse(res.responseText));
                    } catch (e) {
                        createUI(fallbackRoles);
                    }
                },
                onerror: function () {
                    createUI(fallbackRoles);
                }
            });
        } else {
            fetch(`${LOCAL_SERVER}/api/resumes`)
                .then(r => r.json())
                .then(createUI)
                .catch(() => createUI(fallbackRoles));
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", fetchRoles);
    } else {
        fetchRoles();
    }
})();
