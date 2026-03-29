from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os

app = FastAPI()


class MemoCreate(BaseModel):
    title: str
    content: str
    tags: str = ""


def get_db_path():
    return os.getenv("DB_PATH", "memos.db")


def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            important INTEGER NOT NULL DEFAULT 0,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("PRAGMA table_info(memos)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "tags" not in columns:
        cursor.execute("ALTER TABLE memos ADD COLUMN tags TEXT NOT NULL DEFAULT ''")

    if "updated_at" not in columns:
        cursor.execute("ALTER TABLE memos ADD COLUMN updated_at TEXT")

    if "important" not in columns:
        cursor.execute("ALTER TABLE memos ADD COLUMN important INTEGER NOT NULL DEFAULT 0")

    if "done" not in columns:
        cursor.execute("ALTER TABLE memos ADD COLUMN done INTEGER NOT NULL DEFAULT 0")

    conn.commit()
    conn.close()


init_db()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>메모장</title>
        <style>
            * {
                box-sizing: border-box;
            }
            body {
                font-family: Arial, sans-serif;
                max-width: 980px;
                margin: 40px auto;
                padding: 20px;
                background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
                color: #111827;
            }
            h1 {
                margin-bottom: 8px;
                font-size: 34px;
            }
            .subtitle {
                color: #6b7280;
                margin-bottom: 24px;
            }
            .box {
                background: white;
                padding: 22px;
                border-radius: 16px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.06);
                margin-bottom: 20px;
                border: 1px solid #e5e7eb;
            }
            .section-title {
                margin-top: 0;
                margin-bottom: 16px;
                font-size: 20px;
            }
            label {
                display: block;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 6px;
            }
            input, textarea {
                width: 100%;
                padding: 12px 14px;
                margin-bottom: 14px;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                font-size: 14px;
                background: #fff;
            }
            input:focus, textarea:focus {
                outline: none;
                border-color: #111827;
            }
            button {
                padding: 10px 16px;
                border: none;
                border-radius: 10px;
                background: #111827;
                color: white;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
            }
            button:hover {
                opacity: 0.92;
            }
            .secondary {
                background: #6b7280;
            }
            .row {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            .status {
                margin-top: 12px;
                color: #b91c1c;
                font-size: 14px;
            }
            .memo {
                border: 1px solid #e5e7eb;
                border-radius: 14px;
                padding: 18px;
                margin-bottom: 14px;
                background: #fff;
                transition: all 0.15s ease;
            }
            .memo.important {
                border: 2px solid #f59e0b;
                background: #fffaf0;
            }
            .memo.done {
                opacity: 0.62;
                background: #f3f4f6;
            }
            .memo.done .memo-title {
                text-decoration: line-through;
            }
            .memo-title-row {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 10px;
            }
            .memo-title {
                font-size: 19px;
                font-weight: 700;
                line-height: 1.4;
            }
            .icon-buttons {
                display: flex;
                gap: 10px;
                align-items: center;
                font-size: 22px;
            }
            .star, .check {
                cursor: pointer;
                user-select: none;
            }
            .memo-meta {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 12px;
                line-height: 1.7;
            }
            .memo-content {
                margin-bottom: 12px;
                white-space: pre-wrap;
                line-height: 1.6;
            }
            .tags {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-bottom: 14px;
            }
            .tag {
                font-size: 12px;
                padding: 6px 10px;
                border-radius: 999px;
                background: #eef2ff;
                color: #3730a3;
                border: 1px solid #c7d2fe;
            }
            .empty {
                color: #6b7280;
            }
        </style>
    </head>
    <body>
        <h1>내 메모장</h1>
        <div class="subtitle">태그, 중요 표시, 완료 체크까지 되는 메모장</div>

        <div class="box">
            <h2 class="section-title">메모 작성</h2>
            <input type="hidden" id="memoId" />

            <label>제목</label>
            <input type="text" id="title" placeholder="제목을 입력하세요" />

            <label>내용</label>
            <textarea id="content" rows="5" placeholder="내용을 입력하세요"></textarea>

            <label>태그</label>
            <input type="text" id="tags" placeholder="예: 업무, 개인, 아이디어" />

            <div class="row">
                <button onclick="saveMemo()">저장</button>
                <button class="secondary" onclick="resetForm()">초기화</button>
            </div>

            <div class="status" id="status"></div>
        </div>

        <div class="box">
            <h2 class="section-title">검색</h2>
            <input type="text" id="search" placeholder="제목 또는 태그로 검색하세요" />
            <div class="row">
                <button onclick="searchMemos()">검색</button>
                <button class="secondary" onclick="clearSearch()">전체 보기</button>
            </div>
        </div>

        <div class="box">
            <h2 class="section-title">메모 목록</h2>
            <div id="memoList">불러오는 중...</div>
        </div>

        <script>
            async function loadMemos(keyword = '') {
                let url = '/memos';

                if (keyword.trim() !== '') {
                    url += `?keyword=${encodeURIComponent(keyword)}`;
                }

                const response = await fetch(url);
                const result = await response.json();
                const memoList = document.getElementById('memoList');

                if (result.data.length === 0) {
                    memoList.innerHTML = '<p class="empty">조건에 맞는 메모가 없습니다.</p>';
                    return;
                }

                memoList.innerHTML = result.data.map(memo => {
                    const tags = parseTags(memo.tags);
                    const tagsHtml = tags.length
                        ? `<div class="tags">${tags.map(tag => `<span class="tag">#${escapeHtml(tag)}</span>`).join('')}</div>`
                        : '';

                    return `
                        <div class="memo ${memo.important ? 'important' : ''} ${memo.done ? 'done' : ''}">
                            <div class="memo-title-row">
                                <div class="memo-title">
                                    ${memo.important ? '⭐ ' : ''}${escapeHtml(memo.title)}
                                </div>
                                <div class="icon-buttons">
                                    <div class="check" onclick="toggleDone(${memo.id})">
                                        ${memo.done ? '✅' : '☐'}
                                    </div>
                                    <div class="star" onclick="toggleImportant(${memo.id})">
                                        ${memo.important ? '⭐' : '☆'}
                                    </div>
                                </div>
                            </div>

                            <div class="memo-meta">
                                번호: ${memo.id}<br>
                                작성시간: ${memo.created_at}<br>
                                수정시간: ${memo.updated_at ? memo.updated_at : '아직 수정 안 됨'}<br>
                                상태: ${memo.done ? '완료됨' : '진행 중'}
                            </div>

                            ${tagsHtml}

                            <div class="memo-content">${escapeHtml(memo.content)}</div>

                            <div class="row">
                                <button onclick="editMemo(${memo.id})">수정</button>
                                <button class="secondary" onclick="deleteMemo(${memo.id})">삭제</button>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            async function saveMemo() {
                const memoId = document.getElementById('memoId').value;
                const title = document.getElementById('title').value;
                const content = document.getElementById('content').value;
                const tags = document.getElementById('tags').value;
                const status = document.getElementById('status');

                status.textContent = '';

                const payload = {
                    title: title,
                    content: content,
                    tags: tags
                };

                let response;

                if (memoId) {
                    response = await fetch(`/memos/${memoId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });
                } else {
                    response = await fetch('/memos', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });
                }

                const result = await response.json();

                if (!response.ok) {
                    status.textContent = result.detail || '오류가 발생했습니다.';
                    return;
                }

                resetForm();
                searchMemos();
            }

            async function editMemo(id) {
                const response = await fetch(`/memos/${id}`);
                const result = await response.json();

                document.getElementById('memoId').value = result.data.id;
                document.getElementById('title').value = result.data.title;
                document.getElementById('content').value = result.data.content;
                document.getElementById('tags').value = result.data.tags || '';
                document.getElementById('status').textContent = '수정 모드입니다. 내용을 바꾼 뒤 저장을 누르세요.';
            }

            async function deleteMemo(id) {
                const ok = confirm('정말 삭제할까요?');
                if (!ok) return;

                const response = await fetch(`/memos/${id}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (!response.ok) {
                    document.getElementById('status').textContent = result.detail || '삭제 중 오류가 발생했습니다.';
                    return;
                }

                resetForm();
                searchMemos();
            }

            async function toggleImportant(id) {
                const response = await fetch(`/memos/${id}/important`, {
                    method: 'PATCH'
                });

                const result = await response.json();

                if (!response.ok) {
                    document.getElementById('status').textContent = result.detail || '중요 상태 변경 중 오류가 발생했습니다.';
                    return;
                }

                searchMemos();
            }

            async function toggleDone(id) {
                const response = await fetch(`/memos/${id}/done`, {
                    method: 'PATCH'
                });

                const result = await response.json();

                if (!response.ok) {
                    document.getElementById('status').textContent = result.detail || '완료 상태 변경 중 오류가 발생했습니다.';
                    return;
                }

                searchMemos();
            }

            function searchMemos() {
                const keyword = document.getElementById('search').value;
                loadMemos(keyword);
            }

            function clearSearch() {
                document.getElementById('search').value = '';
                loadMemos();
            }

            function resetForm() {
                document.getElementById('memoId').value = '';
                document.getElementById('title').value = '';
                document.getElementById('content').value = '';
                document.getElementById('tags').value = '';
                document.getElementById('status').textContent = '';
            }

            function parseTags(tagsText) {
                if (!tagsText) return [];
                return tagsText
                    .split(',')
                    .map(tag => tag.trim())
                    .filter(tag => tag !== '');
            }

            function escapeHtml(text) {
                return String(text)
                    .replaceAll('&', '&amp;')
                    .replaceAll('<', '&lt;')
                    .replaceAll('>', '&gt;')
                    .replaceAll('"', '&quot;')
                    .replaceAll("'", '&#039;');
            }

            loadMemos();
        </script>
    </body>
    </html>
    """


@app.post("/memos")
def create_memo(memo: MemoCreate):
    if memo.title.strip() == "":
        raise HTTPException(status_code=400, detail="제목은 비워둘 수 없습니다.")

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_tags = ", ".join(
        [tag.strip() for tag in memo.tags.split(",") if tag.strip() != ""]
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO memos (title, content, tags, created_at, updated_at, important, done) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (memo.title, memo.content, clean_tags, created_at, None, 0, 0)
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {
        "success": True,
        "message": "메모가 저장되었습니다.",
        "data": {
            "id": new_id,
            "title": memo.title,
            "content": memo.content,
            "tags": clean_tags,
            "created_at": created_at,
            "updated_at": None,
            "important": 0,
            "done": 0
        }
    }


@app.get("/memos")
def get_memos(keyword: str = Query(default="")):
    conn = get_db_connection()
    cursor = conn.cursor()

    if keyword.strip() == "":
        cursor.execute("SELECT * FROM memos ORDER BY important DESC, done ASC, id DESC")
    else:
        like_keyword = f"%{keyword}%"
        cursor.execute(
            "SELECT * FROM memos WHERE title LIKE ? OR tags LIKE ? ORDER BY important DESC, done ASC, id DESC",
            (like_keyword, like_keyword)
        )

    rows = cursor.fetchall()
    conn.close()

    memos = [dict(row) for row in rows]

    return {
        "success": True,
        "data": memos
    }


@app.get("/memos/{memo_id}")
def get_memo(memo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="해당 메모를 찾을 수 없습니다.")

    return {
        "success": True,
        "data": dict(row)
    }


@app.put("/memos/{memo_id}")
def update_memo(memo_id: int, memo: MemoCreate):
    if memo.title.strip() == "":
        raise HTTPException(status_code=400, detail="제목은 비워둘 수 없습니다.")

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_tags = ", ".join(
        [tag.strip() for tag in memo.tags.split(",") if tag.strip() != ""]
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    existing = cursor.fetchone()

    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="해당 메모를 찾을 수 없습니다.")

    cursor.execute(
        "UPDATE memos SET title = ?, content = ?, tags = ?, updated_at = ? WHERE id = ?",
        (memo.title, memo.content, clean_tags, updated_at, memo_id)
    )

    conn.commit()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return {
        "success": True,
        "message": "메모가 수정되었습니다.",
        "data": dict(updated_row)
    }


@app.patch("/memos/{memo_id}/important")
def toggle_important(memo_id: int):
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="해당 메모를 찾을 수 없습니다.")

    new_important = 0 if row["important"] == 1 else 1

    cursor.execute(
        "UPDATE memos SET important = ?, updated_at = ? WHERE id = ?",
        (new_important, updated_at, memo_id)
    )

    conn.commit()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return {
        "success": True,
        "message": "중요 상태가 변경되었습니다.",
        "data": dict(updated_row)
    }


@app.patch("/memos/{memo_id}/done")
def toggle_done(memo_id: int):
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="해당 메모를 찾을 수 없습니다.")

    new_done = 0 if row["done"] == 1 else 1

    cursor.execute(
        "UPDATE memos SET done = ?, updated_at = ? WHERE id = ?",
        (new_done, updated_at, memo_id)
    )

    conn.commit()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return {
        "success": True,
        "message": "완료 상태가 변경되었습니다.",
        "data": dict(updated_row)
    }


@app.delete("/memos/{memo_id}")
def delete_memo(memo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="해당 메모를 찾을 수 없습니다.")

    deleted_memo = dict(row)

    cursor.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "메모가 삭제되었습니다.",
        "data": deleted_memo
    }