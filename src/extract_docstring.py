"""
Script tự động trích xuất Docstring từ các file nguồn trong dự án.
Nhiệm vụ: Duyệt qua danh sách file, đọc nội dung và ghi lại các đoạn Docstring vào file tài liệu.
"""
import os
import ast


def get_docs_from_file(filepath: str) -> str:
    """
    Sử dụng thư viện ast để phân tích cú pháp file mà không cần chạy code.
    Input:  filepath (str) - Đường dẫn tới file .py.
    Output: (str)          - Toàn bộ docstring của file, class và function.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"[SyntaxError khi parse {filepath}: {e}]\n"

    docs = []

    # 1. Docstring của cả file
    file_doc = ast.get_docstring(tree)
    if file_doc:
        docs.append(f"FILE: {os.path.basename(filepath)}\n{file_doc}\n{'─'*40}")

    # 2. Docstring của Class, FunctionDef, AsyncFunctionDef
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc:
                if isinstance(node, ast.ClassDef):
                    prefix = "CLASS"
                else:
                    prefix = "  METHOD/FUNC"
                docs.append(f"{prefix}: {node.name}\n{doc}\n")

    return "\n".join(docs)


def main():
    """
    Hàm chính: quét toàn bộ file trong project và xuất ra README_DOCS.txt.
    Đặt script này ở thư mục gốc (cùng cấp với src/) rồi chạy.
    """
    base = "src"
    files = [
        f"{base}/constants.py",
        f"{base}/main.py",
        f"{base}/managers/buff_manager.py",
        f"{base}/managers/camera.py",
        f"{base}/managers/game_managers.py",
        f"{base}/managers/quadtree.py",
        f"{base}/entities/__init__.py",
        f"{base}/entities/player.py",
        f"{base}/entities/enemy.py",
        f"{base}/entities/boss.py",
        f"{base}/entities/projectile.py",
    ]

    output_path = "README_DOCS.txt"
    written = 0

    with open(output_path, "w", encoding="utf-8") as out:
        out.write("# LEAGUE OF CHICKENS — AUTO-GENERATED DOCSTRING REFERENCE\n")
        out.write("=" * 60 + "\n\n")

        for filepath in files:
            if not os.path.exists(filepath):
                out.write(f"[SKIP] File không tồn tại: {filepath}\n\n")
                continue

            out.write(f"{'='*60}\n")
            out.write(f"  {filepath}\n")
            out.write(f"{'='*60}\n\n")
            content = get_docs_from_file(filepath)
            out.write(content if content.strip() else "[Không có docstring]\n")
            out.write("\n\n")
            written += 1

    print(f"✓ Đã xuất {written}/{len(files)} file → {output_path}")


if __name__ == "__main__":
    main()