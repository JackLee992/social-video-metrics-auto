#!/usr/bin/env python3
"""
Bootstrap a local workspace for the social-video-metrics-auto project.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


GITIGNORE = """config.json
.env
node_modules/
playwright/.cache/
auth/
raw/
reports/
logs/
"""


PACKAGE_JSON = {
    "name": "social-video-metrics-auto",
    "private": True,
    "version": "0.1.0",
    "type": "module",
    "scripts": {
        "init": "tsx src/cli.ts init",
        "login": "tsx src/cli.ts login",
        "collect": "tsx src/cli.ts collect",
        "report": "tsx src/cli.ts report",
        "publish-feishu": "tsx src/cli.ts publish-feishu",
        "run-daily": "tsx src/cli.ts run-daily",
        "install-launch-agent": "tsx src/cli.ts install-launch-agent"
    },
    "dependencies": {
        "playwright": "^1.53.0",
        "zod": "^3.25.0",
        "date-fns": "^4.1.0",
        "gray-matter": "^4.0.3",
        "json2csv": "^6.0.0-alpha.2"
    },
    "devDependencies": {
        "@types/node": "^24.0.0",
        "tsx": "^4.20.0",
        "typescript": "^5.8.0"
    }
}


TSCONFIG = {
    "compilerOptions": {
        "target": "ES2022",
        "module": "NodeNext",
        "moduleResolution": "NodeNext",
        "strict": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "outDir": "dist"
    },
    "include": ["src/**/*.ts"]
}


CONFIG_EXAMPLE = {
    "outputRoot": ".",
    "timezone": "Asia/Shanghai",
    "platforms": {
        "xiaohongshu": {
            "enabled": True,
            "loginUrl": "https://creator.xiaohongshu.com/",
            "dataUrl": "",
            "storageStatePath": "auth/xiaohongshu.json",
            "selectors": {
                "tableRow": "",
                "title": "",
                "publishTime": "",
                "views7d": "",
                "likes": "",
                "comments": "",
                "shares": "",
                "favorites": "",
                "followersGained": ""
            }
        },
        "douyin": {
            "enabled": True,
            "loginUrl": "https://creator.douyin.com/",
            "dataUrl": "",
            "storageStatePath": "auth/douyin.json",
            "selectors": {
                "tableRow": "",
                "title": "",
                "publishTime": "",
                "views7d": "",
                "likes": "",
                "comments": "",
                "shares": "",
                "favorites": "",
                "followersGained": ""
            }
        },
        "wechat_channels": {
            "enabled": True,
            "loginUrl": "https://channels.weixin.qq.com/",
            "dataUrl": "",
            "storageStatePath": "auth/wechat_channels.json",
            "selectors": {
                "tableRow": "",
                "title": "",
                "publishTime": "",
                "views7d": "",
                "likes": "",
                "comments": "",
                "shares": "",
                "favorites": "",
                "followersGained": ""
            }
        }
    },
    "feishu": {
        "enabled": False,
        "appIdEnv": "FEISHU_APP_ID",
        "appSecretEnv": "FEISHU_APP_SECRET",
        "spaceId": "",
        "parentNodeToken": ""
    },
    "schedule": {
        "hour": 9,
        "minute": 0,
        "label": "com.codex.social-video-metrics-auto"
    }
}


CLI_PLACEHOLDER = """export async function runCli(argv: string[]) {
  const [command = "help"] = argv;

  switch (command) {
    case "init":
    case "login":
    case "collect":
    case "report":
    case "publish-feishu":
    case "run-daily":
    case "install-launch-agent":
      console.log(`[todo] implement ${command}`);
      return;
    default:
      console.log("Commands: init, login, collect, report, publish-feishu, run-daily, install-launch-agent");
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runCli(process.argv.slice(2));
}
"""


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def ensure_file(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".", help="Target automation workspace")
    args = parser.parse_args()

    root = Path(args.workspace).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    for dirname in ["auth", "raw", "reports", "logs", "src", "src/collectors", "src/lib"]:
        (root / dirname).mkdir(parents=True, exist_ok=True)

    ensure_file(root / ".gitignore", GITIGNORE)
    if not (root / "package.json").exists():
        write_json(root / "package.json", PACKAGE_JSON)
    if not (root / "tsconfig.json").exists():
        write_json(root / "tsconfig.json", TSCONFIG)
    if not (root / "config.json.example").exists():
        write_json(root / "config.json.example", CONFIG_EXAMPLE)
    ensure_file(root / ".env.example", "FEISHU_APP_ID=\nFEISHU_APP_SECRET=\n")
    ensure_file(root / "src/cli.ts", CLI_PLACEHOLDER)

    print(f"Initialized workspace: {root}")
    print("Next steps:")
    print("1. Copy config.json.example to config.json and fill real URLs/selectors")
    print("2. Implement src/cli.ts and platform collectors")
    print("3. Run npm install and npx playwright install chromium")


if __name__ == "__main__":
    main()
