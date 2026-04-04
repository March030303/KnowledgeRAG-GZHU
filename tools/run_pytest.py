import subprocess

result = subprocess.run(
    [
        r"C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\RagBackend\.venv\Scripts\python.exe",
        "-m", "pytest",
        "tests/test_tooling_smoke.py",
        "tests/test_trace_logging_unit.py",
        "tests/test_exceptions_unit.py",
        "tests/test_audit_log_unit.py",
        "--cov=trace_logging",
        "--cov=audit",
        "--cov=exception",
        "--cov-report=term-missing",
        "-q",
    ],
    cwd=r"C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\RagBackend",
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)

print(result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout)
if result.returncode != 0 and result.stderr:
    print("STDERR:", result.stderr[-1000:])
print("Exit code:", result.returncode)
