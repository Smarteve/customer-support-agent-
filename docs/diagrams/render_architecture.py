"""Render the architecture diagram as PNG and SVG using matplotlib."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUTPUT = Path(__file__).resolve().parent
fig, ax = plt.subplots(figsize=(16, 12))
fig.patch.set_facecolor("#f8fafc")
ax.set_facecolor("#f8fafc")
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis("off")


def box(x, y, title, detail, color="#e0f2fe", width=3.4, height=1.1):
    ax.add_patch(
        FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.04,rounding_size=0.13",
            facecolor=color,
            edgecolor="#475569",
            linewidth=1.5,
            zorder=3,
        )
    )
    ax.text(x, y + 0.15, title, ha="center", va="center", fontsize=12,
            weight="bold", color="#0f172a", zorder=4)
    ax.text(x, y - 0.22, detail, ha="center", va="center", fontsize=10,
            color="#334155", zorder=4)


def arrow(start, end, label, text_at, both=False, color="#475569"):
    ax.add_patch(
        FancyArrowPatch(start, end, arrowstyle="<->" if both else "-|>",
                        mutation_scale=16, linewidth=1.7, color=color,
                        zorder=2)
    )
    ax.text(*text_at, label, ha="center", va="center", fontsize=10,
            color="#334155", linespacing=1.4,
            bbox={"facecolor": "#f8fafc", "edgecolor": "none", "pad": 3},
            zorder=5)


ax.text(0.3, 11.6, "AI Customer Support Engine", fontsize=23,
        weight="bold", color="#0f172a")
ax.text(0.3, 11.12, "Redis Pub/Sub for live notices · PostgreSQL for saved history · SSE for the browser",
        fontsize=12, color="#475569")

box(2, 10, "Event Source / Simulator", "Sends to our webhook endpoint", "#f1f5f9")
box(7, 10, "FastAPI", "Webhooks + Status API")
box(13, 10, "React Dashboard", "Traces · approvals · ticket inbox", "#ede9fe", width=4)
box(13, 7.5, "PostgreSQL", "Messages · run status · event history", "#dcfce7", width=4)
box(7, 7.5, "Redis", "RQ job queue + Pub/Sub channel", "#ffedd5")
box(7, 4.2, "Agent Worker", "Model loop · validation · policy checks", height=1.3)
box(2, 4.2, "LLM API", "Model requests and results", "#ede9fe")
box(13, 4.2, "Mock Enterprise APIs", "Orders · payments · refund effects", width=4)

arrow((3.75, 10), (5.25, 10), "POST\n/webhooks", (4.5, 10.48))
arrow((8.75, 10), (10.95, 10), "REST commands ←\nSSE events →", (9.85, 10.55), both=True)
arrow((8.75, 9.5), (11, 8.1), "Save input / load history\nOn connection or notice", (11.5, 8.95), both=True, color="#376b56")
arrow((6.55, 9.4), (6.55, 8.1), "Enqueue run ID ↓", (4.9, 8.8))
arrow((7.45, 8.1), (7.45, 9.4), "Pub/Sub notice ↑", (8.55, 8.7), color="#a3442e")
arrow((6.55, 6.9), (6.55, 4.9), "Consume job ↓", (4.95, 5.9))
arrow((7.45, 4.9), (7.45, 6.9), "Publish after commit ↑", (8.8, 6.35), color="#a3442e")
arrow((8.75, 4.8), (11.6, 6.9), "Save start, steps,\nresult, or failure", (11.6, 5.65), color="#376b56")
arrow((3.75, 4.2), (5.25, 4.2), "Model calls", (4.5, 4.7), both=True)
arrow((8.75, 4.2), (10.95, 4.2), "Checked tool calls", (9.85, 4.7), both=True)

ax.text(0.6, 2.3, "LIVE PATH:  Worker → Redis Pub/Sub → FastAPI SSE → React Dashboard",
        fontsize=13, color="#a3442e", weight="bold")
ax.text(0.6, 1.45, "Commit the state and event in PostgreSQL before publishing the notice.\nOne Redis deployment has two separate roles. Load saved history on connect or notification.",
        fontsize=12, color="#475569", linespacing=1.8)

fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
for extension in ("png", "svg"):
    fig.savefig(OUTPUT / f"architecture.{extension}", dpi=160,
                facecolor=fig.get_facecolor())
    if extension == "svg":
        path = OUTPUT / "architecture.svg"
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
plt.close(fig)

# Focused view of the live path, using the same drawing helpers.
fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor("#f8fafc")
ax.set_facecolor("#f8fafc")
ax.set_xlim(0, 16)
ax.set_ylim(0, 7)
ax.axis("off")
ax.text(0.3, 6.55, "Live progress: Redis Pub/Sub → SSE", fontsize=23,
        weight="bold", color="#0f172a")
box(2, 4.8, "Agent Worker", "Saves each step before publish")
box(7, 4.8, "Redis Pub/Sub", "Broadcasts to subscribed APIs", "#ffedd5")
box(12.5, 4.8, "FastAPI SSE Endpoint", "Reads saved events on notice", width=4)
box(2, 1.4, "PostgreSQL", "Run state + ordered event history", "#dcfce7")
box(12.5, 1.4, "React Dashboard", "Status + execution timeline", "#ede9fe", width=4)
arrow((3.75, 4.8), (5.25, 4.8), "After commit:\nPUBLISH", (4.5, 5.5), color="#a3442e")
arrow((8.75, 4.8), (10.45, 4.8), "Push notice", (9.6, 5.3), color="#a3442e")
arrow((2, 4.2), (2, 2), "Save state\nand event", (0.8, 3.1), color="#376b56")
arrow((12.5, 4.2), (12.5, 2), "SSE stream", (13.8, 3.1), color="#a3442e")
arrow((10.45, 4.2), (3.75, 1.8), "Read saved events\non notice or reconnect", (7, 2.8), both=True, color="#376b56")
fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
for extension in ("png", "svg"):
    fig.savefig(OUTPUT / f"streaming.{extension}", dpi=160,
                facecolor=fig.get_facecolor())
    if extension == "svg":
        path = OUTPUT / "streaming.svg"
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
plt.close(fig)
