import compileall
import os
import subprocess
import sys
import tempfile


class ApplicationUpdateService:
    def __init__(self, project_root, branch="NewClockVersion"):
        self.project_root = project_root
        self.branch = branch

    def _run(self, command, cwd=None, timeout=120):
        return subprocess.run(
            command,
            cwd=cwd or self.project_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def available_commits(self):
        fetch = self._run(["git", "fetch", "--quiet", "origin", self.branch], timeout=30)
        if fetch.returncode:
            raise RuntimeError("Repository konnte nicht erreicht werden.")
        result = self._run(
            ["git", "rev-list", "--count", f"HEAD..origin/{self.branch}"]
        )
        if result.returncode:
            raise RuntimeError("Update-Stand konnte nicht ermittelt werden.")
        return int(result.stdout.strip())

    def install_and_validate(self):
        count = self.available_commits()
        if count == 0:
            return False, "Die Anwendung ist bereits aktuell."

        ancestor = self._run(
            ["git", "merge-base", "--is-ancestor", "HEAD", f"origin/{self.branch}"]
        )
        if ancestor.returncode:
            return False, "Lokale Änderungen verhindern ein sicheres Update."

        with tempfile.TemporaryDirectory(prefix="prayerclock-update-") as temp_dir:
            archive_path = os.path.join(temp_dir, "update.tar")
            archive = self._run(
                ["git", "archive", f"origin/{self.branch}", "-o", archive_path]
            )
            if archive.returncode:
                return False, "Der neue Stand konnte nicht vorbereitet werden."
            extract = self._run(["tar", "-xf", archive_path, "-C", temp_dir])
            if extract.returncode:
                return False, "Der neue Stand konnte nicht entpackt werden."

            requirements = os.path.join(temp_dir, "requirements.txt")
            dependencies = self._run(
                [sys.executable, "-m", "pip", "install", "-r", requirements],
                timeout=600,
            )
            if dependencies.returncode:
                return False, "Abhängigkeiten des Updates konnten nicht installiert werden."

            if not compileall.compile_dir(
                os.path.join(temp_dir, "src"), quiet=1, force=True
            ):
                return False, "Der neue Programmcode konnte nicht kompiliert werden."

            health = self._run(
                [sys.executable, os.path.join(temp_dir, "src", "PrayerTimeClock.py"), "--health-check"],
                cwd=temp_dir,
                timeout=30,
            )
            if health.returncode:
                return False, "Der Starttest der neuen Version ist fehlgeschlagen."

        update = self._run(["git", "merge", "--ff-only", f"origin/{self.branch}"])
        if update.returncode:
            return False, "Das Update konnte nicht sicher übernommen werden."
        return True, f"{count} Update{'s' if count != 1 else ''} installiert."
