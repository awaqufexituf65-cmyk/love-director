"""Love Director Engine — full pipeline test."""
import sys
sys.path.insert(0, 'src')
from pathlib import Path
from director import LoveDirectorEngine


def main():
    engine = LoveDirectorEngine(data_dir=Path('../../data'))
    sid = engine.start_session()

    steps = [
        ('phase_0', {}),
        ('phase_1a', {
            'age': 31, 'gender': 'female', 'city_tier': '二线城市',
            'parent_marriage': '和睦', 'relationship_count': 2,
            'purpose': 'marriage_oriented',
        }),
        ('phase_1b', {
            'chat_texts': [open('test_data/chat1.txt', encoding='utf-8').read()],
        }),
        ('phase_1c', {}),
        ('phase_2', {
            'time_belief': {'type': '闪电型'},
            'purpose': 'marriage_oriented',
            'value_ranking': {'claimed': {'1st': '性格'}, 'actual': {'1st': '经济条件'}},
            'conflict_belief': {'type': 'avoidance'},
            'giving_pattern': {},
        }),
        ('phase_3', {}),
        ('phase_4', {}),
    ]

    for name, data in steps:
        r = engine.process_phase(sid, name, data)

        if name == 'phase_1b':
            cross = r.get('cross_analysis', {})
            print(f"[{name}] conflict_avoidance = {cross.get('avg_conflict_avoidance', 0):.2f}")
        elif name == 'phase_1c':
            print(f"[{name}] gaps = {r.get('gap_count', 0)}, vulnerability = {r.get('vulnerability_score', 0):.2f}")
        elif name == 'phase_4':
            print(f"\n{'=' * 55}")
            print(f"  LOVE DECISION TREE")
            print(f"  Variables: {r.get('variable_count', 0)}")
            print(f"  Validation: {'PASS' if r.get('validation_passed') else r.get('validation_issues', [])}")
            print(f"{'=' * 55}\n")

            tree = r.get('tree', {})

            def show(node, depth=0):
                pre = "  " * depth
                t = node.get('type', '')
                if t == 'variable':
                    v = node.get('variable', {})
                    print(f"{pre}{v.get('description', '?')}")
                elif t == 'branch':
                    b = node.get('branch', {})
                    p = b.get('probability', {}).get('display', '?')
                    print(f"{pre}|-- [{b.get('direction', '?')}] {p}")
                elif t == 'stochastic_event':
                    ev = node.get('event', {})
                    print(f"{pre}   ~ {ev.get('name', '?')}")
                elif t == 'ending':
                    e = node.get('ending', {})
                    p = e.get('probability', {}).get('display', '?')
                    em = e.get('emoji', '')
                    print(f"{pre}     {em} {e.get('title', '?')[:55]} [{p}] {e.get('timeframe', '?')}")

                for child in node.get('children', []):
                    show(child, depth + 1)

            show(tree)

            # Count endings
            def collect_endings(node):
                result = []
                if node.get('type') == 'ending':
                    result.append(node.get('ending', {}).get('type', ''))
                for c in node.get('children', []):
                    result.extend(collect_endings(c))
                return result

            ends = collect_endings(tree)
            etypes = set(ends)
            print(f"\n  Endings: {len(ends)}")
            print(f"  Types: {len(etypes)} ({', '.join(sorted(etypes))})")

        else:
            print(f"[{name}] ok")

    # Phase 5
    engine.process_phase(sid, 'phase_5', {})
    engine.store.delete_session(sid)
    print("\nEngine pipeline complete.")


if __name__ == '__main__':
    main()
