"""Create a single-file HTML explorer alongside the editable static Site."""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
html = (DIST / "index.html").read_text()
html = html.replace('<link rel="stylesheet" href="styles.css">',
                    '<style>\n' + (DIST / "styles.css").read_text() + '\n</style>')
html = html.replace('<script defer src="data.js"></script>', '')
html = html.replace('<script defer src="app.js"></script>', '')
html = html.replace('href="design.md"', 'href="dist/design.md"')
html = html.replace('href="obsidian-notes.zip"', 'href="dist/obsidian-notes.zip"')
html = html.replace('</body>', '<script>\n' + (DIST / "data.js").read_text() +
                    '\n</script><script>\n' + (DIST / "app.js").read_text() + '\n</script>\n</body>')
html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
(ROOT / "project-explorer.html").write_text(html)
with zipfile.ZipFile(ROOT / "support-engine-explorer.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    archive.write(ROOT / "project-explorer.html", "support-engine-explorer/project-explorer.html")
    for p in sorted(DIST.rglob("*")):
        if p.is_file():
            archive.write(p, Path("support-engine-explorer/dist") / p.relative_to(DIST))
print("Built self-contained project-explorer.html and portable explorer zip.")
