# -*- coding: utf-8 -*-
"""PreToolUse-hook: перед `git commit` прогоняет pytest и при падении блокирует
коммит (exit 2 → причина уходит обратно агенту). На любые другие Bash-команды
выходит мгновенно (exit 0). Прописан в .claude/settings.json.

Вход — JSON от Claude Code на stdin: {"tool_input": {"command": "..."}, ...}.
"""
import sys, json, subprocess, os

try:                       # читаемая кириллица в причине (cp1251-консоль)
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # нет/битый ввод — не мешаем работе
    cmd = ((data.get("tool_input") or {}).get("command") or "")
    # реагируем только на настоящий commit (не на git log/status/diff/add)
    if "git commit" not in cmd:
        sys.exit(0)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py = os.path.join(root, ".venv", "Scripts", "python.exe")
    if not os.path.isfile(py):
        py = sys.executable
    res = subprocess.run([py, "-m", "pytest", "-q"], cwd=root,
                         capture_output=True, text=True)
    if res.returncode != 0:
        tail = (res.stdout or "")[-2500:] + (res.stderr or "")[-800:]
        print("PreToolUse: pytest упал — коммит остановлен.\n"
              "Почини тесты (или, если падение не связано с правкой, скажи об "
              "этом явно).\n\n" + tail, file=sys.stderr)
        sys.exit(2)   # блокируем git commit
    sys.exit(0)


if __name__ == "__main__":
    main()
