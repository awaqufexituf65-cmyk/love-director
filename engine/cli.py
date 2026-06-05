#!/usr/bin/env python3
"""Love Director CLI — Command-line interface for the relationship pattern analysis engine.

Usage:
    love-director analyze --chat chat_export.txt
    love-director analyze --chats export1.txt export2.txt export3.txt
    love-director profile --self-report profile.json
    love-director tree --session <session_id>
"""

import json
import sys
from pathlib import Path

# Add engine/src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from director import LoveDirectorEngine


def cmd_analyze(args: dict) -> int:
    """Analyze chat records and generate a decision tree."""
    engine = LoveDirectorEngine(data_dir=Path(__file__).parent.parent / "data")

    # Start session
    session_id = engine.start_session()

    # Process safety
    print("🎬 Love Director — 开始分析")
    print("Phase 0: 安全声明已确认\n")

    # Phase 1A: Self-report (minimal from CLI)
    profile = {
        "age": args.get("age", 25),
        "gender": args.get("gender", "未提供"),
        "city_tier": args.get("city", "未提供"),
        "parent_marriage": args.get("parents", "未提供"),
        "relationship_count": args.get("relationships", 0),
    }
    result = engine.process_phase(session_id, "phase_1a", profile)
    print(f"Phase 1A: 画像采集完成 — {result['fields_collected']}")

    # Phase 1B: Chat analysis
    chat_paths = args.get("chat_paths", [])
    if not chat_paths:
        print("❌ 需要至少一个聊天记录文件")
        print("用法: love-director analyze --chats file1.txt file2.txt")
        return 1

    chat_texts = []
    for cp in chat_paths:
        path = Path(cp)
        if not path.exists():
            print(f"⚠️ 文件不存在: {cp}")
            continue
        chat_texts.append(path.read_text(encoding="utf-8", errors="ignore"))

    result = engine.process_phase(session_id, "phase_1b", {"chat_texts": chat_texts})
    cross = result.get("cross_analysis", {})
    print(f"Phase 1B: 行为层分析完成")
    print(f"  - 分析了 {result.get('relationship_count', 0)} 段关系")
    print(f"  - 伴侣相似度: {cross.get('partner_similarity', 0):.2f}")
    print(f"  - 冲突回避指数: {cross.get('avg_conflict_avoidance', 0):.2f}")

    # Phase 1C: Gap analysis
    result = engine.process_phase(session_id, "phase_1c", {})
    print(f"Phase 1C: 差距分析发现 {result.get('gap_count', 0)} 个盲区")
    if result.get("vulnerability_score", 0) > 0.5:
        print(f"  ⚠️ 脆弱性评分: {result['vulnerability_score']:.2f} (偏高)\n")

    # Phase 2: Philosophy (minimal from CLI)
    philosophy = {"time_belief": {"type": "未采集"}, "purpose": "未采集",
                  "value_ranking": {}, "conflict_belief": {}, "giving_pattern": {},
                  "social_media_influence": {}, "security_source": {}}
    result = engine.process_phase(session_id, "phase_2", philosophy)
    print(f"Phase 2: 哲学探针 (CLI 模式仅采集基础数据)\n")

    # Phase 3: Observation
    result = engine.process_phase(session_id, "phase_3", {})
    print(f"Phase 3: 行为观测完成\n")

    # Phase 4: Decision tree ★
    print("Phase 4: 🌳 生成决策树...")
    result = engine.process_phase(session_id, "phase_4", {})
    tree = result.get("tree", {})

    print(f"  - 关键变量: {result.get('variable_count', 0)} 个")
    print(f"  - 变量: {', '.join(result.get('variables', []))}")
    print(f"  - 验证: {'✅ 通过' if result.get('validation_passed') else '⚠️ 有警告'}")
    if result.get("validation_issues"):
        for issue in result["validation_issues"]:
            print(f"    - {issue}")

    # Print tree summary
    _print_tree_summary(tree)

    # Phase 5: Perspective
    engine.process_phase(session_id, "phase_5", {})
    print("\n🎥 导演视角: 四种问题已呈现。你是你自己的导演。")

    # Cleanup
    engine.store.delete_session(session_id)
    return 0


def _print_tree_summary(tree: dict, indent: int = 0) -> None:
    """Print a readable summary of the decision tree."""
    prefix = "  " * indent
    label = tree.get("label", "")
    t = tree.get("type", "")

    if t == "variable":
        var = tree.get("variable", {})
        print(f"{prefix}🔀 {var.get('description', label)} (gap: {var.get('self_report_gap', 0):.2f}, consistency: {var.get('cross_relationship_consistency', 0):.2f})")
    elif t == "branch":
        b = tree.get("branch", {})
        prob = b.get("probability", {}).get("display", "")
        print(f"{prefix}├─ {b.get('label', label)} — {prob}")
    elif t == "stochastic_event":
        ev = tree.get("event", {})
        print(f"{prefix}   ├─ 🎲 {ev.get('name', label)}")
    elif t == "ending":
        e = tree.get("ending", {})
        print(f"{prefix}      🍂 {e.get('title', label)} [{e.get('emoji', '')} {e.get('type', '')}] — {e.get('probability', {}).get('display', '')}")

    for child in tree.get("children", []):
        _print_tree_summary(child, indent + 1)


def cmd_profile(args: dict) -> int:
    """Generate profile from self-report JSON."""
    engine = LoveDirectorEngine()
    session_id = engine.start_session()

    report_path = args.get("self_report_path")
    if report_path:
        with open(report_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
    else:
        print("❌ 需要 --self-report profile.json")
        return 1

    result = engine.process_phase(session_id, "phase_1a", profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    engine.store.delete_session(session_id)
    return 0


def cmd_tree(args: dict) -> int:
    """Regenerate decision tree from existing session."""
    session_id = args.get("session_id")
    if not session_id:
        print("❌ 需要 --session <session_id>")
        return 1

    engine = LoveDirectorEngine()
    result = engine.process_phase(session_id, "phase_4", {})
    print(json.dumps(result.get("tree", {}), ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Love Director — 恋爱观观测与导演系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  love-director analyze --chats chat1.txt chat2.txt chat3.txt
  love-director analyze --chat export.txt --age 28 --city "上海"
  love-director profile --self-report profile.json
        """,
    )

    sub = parser.add_subparsers(dest="command")

    # analyze
    analyze = sub.add_parser("analyze", help="分析聊天记录并生成决策树")
    analyze.add_argument("--chats", nargs="+", help="聊天记录文件路径 (WeFlow TXT格式)")
    analyze.add_argument("--chat", help="单个聊天记录文件")
    analyze.add_argument("--age", type=int, default=25)
    analyze.add_argument("--gender", default="未提供")
    analyze.add_argument("--city", default="未提供")
    analyze.add_argument("--parents", default="未提供")
    analyze.add_argument("--relationships", type=int, default=0)

    # profile
    prof = sub.add_parser("profile", help="从JSON生成画像")
    prof.add_argument("--self-report", dest="self_report_path", help="自述JSON文件")

    # tree
    tree_cmd = sub.add_parser("tree", help="重新生成决策树")
    tree_cmd.add_argument("--session", dest="session_id", help="会话ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    cmd_args = vars(args)
    if args.command == "analyze":
        # Normalize --chat into --chats
        if cmd_args.get("chat") and not cmd_args.get("chats"):
            cmd_args["chats"] = [cmd_args["chat"]]
        if cmd_args.get("chats"):
            cmd_args["chat_paths"] = cmd_args["chats"]
        return cmd_analyze(cmd_args)
    elif args.command == "profile":
        return cmd_profile({"self_report_path": cmd_args.get("self_report_path")})
    elif args.command == "tree":
        return cmd_tree({"session_id": cmd_args.get("session_id")})

    return 0


if __name__ == "__main__":
    sys.exit(main())
