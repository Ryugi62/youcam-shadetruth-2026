"""API 키 로딩: 환경변수 YOUCAM_API_KEY, 없으면 .env 파일. 키를 출력하지 않는다."""
import os


def load_key(env_path: str = ".env") -> str:
    k = os.environ.get("YOUCAM_API_KEY", "").strip()
    if k:
        return k
    try:
        for line in open(env_path, encoding="utf-8"):
            if line.startswith("YOUCAM_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""
