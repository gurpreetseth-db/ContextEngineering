"""Build all three decks into slides/*.html. Run:  python3 slides/_build/build.py"""
import pathlib, importlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
out = pathlib.Path(__file__).parent.parent
for mod, name in (("deck_1", "session1_foundations_governance_genie"), ("deck_2", "session2_retrieval_memory_tools"), ("deck_3", "session3_multiagent_runtime_apps_eval")):
    d = importlib.import_module(mod).build()
    p = out / f"{name}.html"; p.write_text(d.render())
    print(f"{p.name}: {len(d.slides)} slides, {p.stat().st_size // 1024} KB")
