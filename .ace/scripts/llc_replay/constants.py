from pathlib import Path

CACHE_DIR = Path(".ace/cache")
LOGS_DIR = Path(".ace/logs")

RED_ZONE_PATTERNS = [
    "**/schema.prisma", "**/migrations/**",
    "**/*.guard.ts", "**/*.strategy.ts",
    "**/auth/**", "**/middleware/**",
    ".env", ".env.*", "**/config/**",
    ".github/workflows/**", "**/ci.yml"
]
