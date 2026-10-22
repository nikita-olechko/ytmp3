import re
from urllib.parse import quote

from flask import Blueprint, Response, jsonify, render_template, request

from web.auth.guard import login_required
from web.converter.youtube import QUALITIES, ConversionError, to_mp3

convert_bp = Blueprint("convert", __name__)

CHUNK_SIZE = 256 * 1024


def _safe_filename(title: str) -> str:
    return re.sub(r'[\/*?:"<>|\r\n]', "", title).strip() or "audio"


@convert_bp.get("/")
@login_required
def index():
    return render_template("index.html", qualities=QUALITIES)


@convert_bp.post("/api/convert")
@login_required
def convert():
    body = request.get_json(silent=True) or {}
    try:
        result = to_mp3(body.get("url", "").strip(), str(body.get("quality", "192")))
    except ConversionError as e:
        return jsonify(error=str(e)), 400

    filename = _safe_filename(result.title) + ".mp3"

    def stream():
        # Chunked streaming avoids Cloud Run's 32 MiB buffered response limit
        try:
            with open(result.path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    yield chunk
        finally:
            result.cleanup()

    ascii_name = filename.encode("ascii", "ignore").decode().replace('"', "") or "audio.mp3"
    headers = {
        "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}",
        "X-Filename": quote(filename),
    }
    return Response(stream(), mimetype="audio/mpeg", headers=headers)
