"""Command-line entry point for the isolated pipeline."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from .answers import answers_from_page_contracts, parse_answer_text, write_answer_ledger
from .assemble import assemble_paper
from .assets import AssetStore, clip_figure_from_pdf
from .audit import audit_paper
from .errors import EjuBankError
from .inventory import inventory_status_summary, load_inventory, save_inventory
from .migrations import migrate_database
from .ocr.pipeline import extract_pages
from .ops import check_database, create_backup, restore_backup, run_doctor, verify_backup
from .page_contract import load_page_contracts
from .pdf_pipeline import probe_manifest, render_manifest
from .publish import publish_file
from .server import serve
from .source import create_source_manifest
from .util import load_json


def _path(value: str) -> Path:
    return Path(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eju-bank", description="Independent EJU PDF question-bank pipeline")
    parser.add_argument("--workspace",type=_path,help="Workspace root for relative data paths")
    parser.add_argument("--config",type=_path,help="Workspace configuration JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    # 1. source-init
    command = sub.add_parser("source-init", help="Create a hashed source manifest")
    command.add_argument("--session", required=True)
    command.add_argument("--subject", required=True, choices=["JAPANESE", "SCIENCE", "JAPAN_AND_WORLD", "MATHEMATICS"])
    command.add_argument("--language", default="ja", choices=["ja", "en"])
    command.add_argument("--syllabus-version", required=True)
    command.add_argument("--question-booklet", required=True, type=_path)
    command.add_argument("--answer-key", type=_path)
    command.add_argument("--rights-status", default="PRIVATE_STUDY")
    command.add_argument("--rights-note", default="")
    command.add_argument("--out", required=True, type=_path)

    # 2. probe
    command = sub.add_parser("probe", help="Inspect every PDF page")
    command.add_argument("--manifest", required=True, type=_path)
    command.add_argument("--out", required=True, type=_path)

    # 3. render
    command = sub.add_parser("render", help="Render full pages and overlapping high-resolution tiles")
    command.add_argument("--manifest", required=True, type=_path)
    command.add_argument("--role", required=True, choices=["QUESTION_BOOKLET", "ANSWER_KEY"])
    command.add_argument("--out", required=True, type=_path)
    command.add_argument("--pages")
    command.add_argument("--full-dpi", type=int, default=180)
    command.add_argument("--tile-dpi", type=int, default=320)
    command.add_argument("--tile-count", type=int, default=3)
    command.add_argument("--overlap", type=float, default=0.08)

    # 4. extract
    command = sub.add_parser("extract", help="Run a configured OCR/VLM provider over a render index")
    command.add_argument("--manifest", required=True, type=_path)
    command.add_argument("--render-index", required=True, type=_path)
    command.add_argument("--provider-config", required=True, type=_path)
    command.add_argument("--provider", required=True)
    command.add_argument("--out", required=True, type=_path)
    command.add_argument("--pages", help="Page range or comma-separated list of pages to extract (e.g. 1-5,8)")
    command.add_argument("--retry-failed", action="store_true", help="Only retry pages that failed validation")
    command.add_argument("--resume-run", help="Resume from an existing extraction run ID")
    command.add_argument("--retry", action="store_true", help="Retry all pages (replaces existing output)")

    # 5. validate-pages
    command = sub.add_parser("validate-pages", help="Validate all p*.json page contracts")
    command.add_argument("--pages", required=True, type=_path)

    # 6. parse-answers
    command = sub.add_parser("parse-answers", help="Parse reviewed answer directives")
    command.add_argument("--input", required=True, type=_path)
    command.add_argument("--out", required=True, type=_path)

    # 7. answers-from-pages
    command = sub.add_parser("answers-from-pages", help="Build an answer ledger from reviewed answer-page contracts")
    command.add_argument("--pages", required=True, type=_path)
    command.add_argument("--out", required=True, type=_path)

    # 8. assemble
    command = sub.add_parser("assemble", help="Compile reviewed pages plus independent answers")
    command.add_argument("--manifest", required=True, type=_path)
    command.add_argument("--pages", required=True, type=_path)
    command.add_argument("--answers", type=_path)
    command.add_argument("--out", required=True, type=_path)

    # 9. audit
    command = sub.add_parser("audit", help="Run the paper fail-closed quality gate")
    command.add_argument("--paper", required=True, type=_path)

    # 10. publish
    command = sub.add_parser("publish", help="Publish an immutable paper version into SQLite")
    command.add_argument("--paper", required=True, type=_path)
    command.add_argument("--database", type=_path)
    command.add_argument("--channel", default="PRIVATE", choices=["PRIVATE", "PUBLIC", "COMMERCIAL"])

    # 11. serve
    command = sub.add_parser("serve", help="Serve the local learner API and demo UI")
    command.add_argument("--database", type=_path)
    command.add_argument("--media-dir", type=_path)
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8765)
    command.add_argument("--allow-remote", action="store_true")
    command.add_argument("--token")
    command.add_argument("--workspace-root", type=_path)
    command.add_argument("--allow-host", action="append", default=[])
    command.add_argument("--allow-origin", action="append", default=[])

    # 12. doctor
    command = sub.add_parser("doctor", help="Run environment and system diagnostic checks")
    command.add_argument("--database", type=_path)
    command.add_argument("--media-dir", type=_path)

    # 13. db
    db_cmd = sub.add_parser("db", help="Database migration and maintenance")
    db_sub = db_cmd.add_subparsers(dest="db_action", required=True)
    m_cmd = db_sub.add_parser("migrate", help="Apply schema migrations to database")
    m_cmd.add_argument("--database", type=_path)
    c_cmd = db_sub.add_parser("check", help="Check database schema and foreign key integrity")
    c_cmd.add_argument("--database", type=_path)

    # 14. backup
    bk_cmd = sub.add_parser("backup", help="Manage database and asset backups")
    bk_sub = bk_cmd.add_subparsers(dest="backup_action", required=True)
    bc_cmd = bk_sub.add_parser("create", help="Create a verified backup archive")
    bc_cmd.add_argument("--database", type=_path)
    bc_cmd.add_argument("--inventory", type=_path)
    bc_cmd.add_argument("--media-dir", type=_path)
    bc_cmd.add_argument("--mode",choices=["LEARNING","FULL"],default="LEARNING")
    bc_cmd.add_argument("--out", type=_path, default=Path("library/backups"))
    bv_cmd = bk_sub.add_parser("verify", help="Verify a backup archive")
    bv_cmd.add_argument("--backup", required=True, type=_path)
    br_cmd = bk_sub.add_parser("restore", help="Restore database and assets from backup archive")
    br_cmd.add_argument("--backup", required=True, type=_path)
    br_cmd.add_argument("--target", required=True, type=_path)
    br_cmd.add_argument("--force", action="store_true", help="Overwrite existing files in target")

    # 15. inventory
    inv_cmd = sub.add_parser("inventory", help="Content inventory tracking")
    inv_sub = inv_cmd.add_subparsers(dest="inventory_action", required=True)
    inv_s_cmd = inv_sub.add_parser("status", help="Show inventory status and completion metrics")
    inv_s_cmd.add_argument("--inventory", type=_path)
    inv_i_cmd = inv_sub.add_parser("init", help="Initialize or reset content inventory")
    inv_i_cmd.add_argument("--inventory", type=_path)

    # 16. clip-figure
    clip_cmd = sub.add_parser("clip-figure", help="Clip figure from PDF page into media store")
    clip_cmd.add_argument("--pdf", required=True, type=_path)
    clip_cmd.add_argument("--page", required=True, type=int)
    clip_cmd.add_argument("--bbox", required=True, help="x0,y0,x1,y1 (normalized 0..1)")
    clip_cmd.add_argument("--media-dir", type=_path)
    clip_cmd.add_argument("--dpi", type=int, default=300)

    for name in ['diagnostics','rebuild-projections','retention-preview']:
        cmd=sub.add_parser(name)
        cmd.add_argument('--database',type=_path,default=Path('library/eju.db'))
    audio=sub.add_parser('audio-probe');audio.add_argument('--file',type=_path,required=True)
    return parser


def run(args: argparse.Namespace) -> Any:
    from .workspace import WorkspaceConfig
    ws=WorkspaceConfig.resolve(root=getattr(args,'workspace',None),config=getattr(args,'config',None),database=getattr(args,'database',None),media=getattr(args,'media_dir',None),inventory=getattr(args,'inventory',None))
    for key,value in vars(args).items():
        if isinstance(value,Path) and key not in {'workspace','config','database','media_dir','inventory'} and not value.is_absolute():setattr(args,key,ws.root/value)
    for key,value in [('database',ws.database),('media_dir',ws.media),('inventory',ws.inventory)]:
        if hasattr(args,key):setattr(args,key,value)
    if hasattr(args,'workspace_root') and args.workspace_root is None:args.workspace_root=ws.root
    if args.command=='audio-probe':
        from .audio import probe_audio
        return probe_audio(args.file)
    if args.command in {'diagnostics','rebuild-projections','retention-preview'}:
        from .db import Database
        from .maintenance import diagnostics,retention_plan
        db=Database(args.database)
        try:
            if args.command=='diagnostics':return diagnostics(db)
            if args.command=='retention-preview':return retention_plan(db)
            db.rebuild_search();db.rebuild_attempts();return {'rebuilt':True}
        finally:db.close()
    if args.command == "source-init":
        return create_source_manifest(
            session=args.session,
            subject=args.subject,
            language=args.language,
            syllabus_version=args.syllabus_version,
            question_booklet=args.question_booklet,
            answer_key=args.answer_key,
            rights_status=args.rights_status,
            rights_note=args.rights_note,
            output_path=args.out,
        )
    if args.command == "probe":
        return probe_manifest(args.manifest, args.out)
    if args.command == "render":
        return render_manifest(
            args.manifest,
            role=args.role,
            output_dir=args.out,
            pages=args.pages,
            full_dpi=args.full_dpi,
            tile_dpi=args.tile_dpi,
            tile_count=args.tile_count,
            overlap=args.overlap,
        )
    if args.command == "extract":
        return extract_pages(
            manifest_path=args.manifest,
            render_index_path=args.render_index,
            output_dir=args.out,
            provider_config=args.provider_config,
            provider_name=args.provider,
            pages=args.pages,
            retry_failed=args.retry_failed,
            resume_run=args.resume_run,
            retry=args.retry,
        )
    if args.command == "validate-pages":
        pages = load_page_contracts(args.pages)
        return {"status": "passed", "pages": len(pages)}
    if args.command == "parse-answers":
        ledger = parse_answer_text(args.input.read_text(encoding="utf-8"), source=str(args.input))
        write_answer_ledger(args.out, ledger)
        return {"status": "passed", "entries": len(ledger["entries"]), "out": str(args.out)}
    if args.command == "answers-from-pages":
        ledger = answers_from_page_contracts(args.pages)
        write_answer_ledger(args.out, ledger)
        return {"status": "passed", "entries": len(ledger["entries"]), "out": str(args.out)}
    if args.command == "assemble":
        paper = assemble_paper(
            manifest_path=args.manifest,
            pages_dir=args.pages,
            answer_ledger_path=args.answers,
            output_path=args.out,
        )
        return {"status": "passed", "paperId": paper["paperId"], "questions": paper["questionCount"]}
    if args.command == "audit":
        return audit_paper(load_json(args.paper))
    if args.command == "publish":
        return publish_file(args.paper, args.database, channel=args.channel,media_dir=ws.media,workspace_root=ws.root)
    if args.command == "serve":
        serve(
            args.database,
            media_dir=args.media_dir,
            host=args.host,
            port=args.port,
            allow_remote=args.allow_remote,
            admin_token=args.token,
            workspace_root=args.workspace_root,
            host_allowlist=set(args.allow_host),
            allowed_origins=set(args.allow_origin),
        )
        return None
    if args.command == "doctor":
        return run_doctor(database_path=args.database, media_dir=args.media_dir)
    if args.command == "db":
        if args.db_action == "migrate":
            conn = sqlite3.connect(args.database.expanduser().resolve())
            ver = migrate_database(conn)
            conn.close()
            return {"status": "migrated", "database": str(args.database), "schemaVersion": ver}
        if args.db_action == "check":
            return check_database(args.database)
    if args.command == "backup":
        if args.backup_action == "create":
            res = create_backup(
                database_path=args.database,
                inventory_path=args.inventory,
                media_dir=args.media_dir,
                output_dir=args.out,mode=args.mode,workspace_root=ws.root,
            )
            return {"status": "created", "backupFile": str(res)}
        if args.backup_action == "verify":
            return verify_backup(args.backup)
        if args.backup_action == "restore":
            return restore_backup(args.backup, args.target, overwrite=args.force)
    if args.command == "inventory":
        if args.inventory_action == "status":
            return inventory_status_summary(args.inventory)
        if args.inventory_action == "init":
            save_inventory({"schemaVersion": 1, "items": []}, args.inventory)
            return {"status": "initialized", "path": str(args.inventory)}
    if args.command == "clip-figure":
        bbox = [float(v.strip()) for v in args.bbox.split(",")]
        data, w, h = clip_figure_from_pdf(args.pdf, args.page, bbox, dpi=args.dpi)
        store = AssetStore(args.media_dir)
        res = store.put_bytes(data, mime_type="image/png", ext=".png")
        return {"status": "clipped", "width": w, "height": h, "asset": res}
    raise AssertionError(args.command)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run(args)
    except EjuBankError as exc:
        parser.exit(2, f"error: {exc}\n")
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
