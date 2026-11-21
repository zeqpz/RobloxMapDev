"""Generate studio/StandardSizes.lua (a ModuleScript) from standards/sizes.json so Blender and Studio share one
source of truth.   python tools/gen_luau_sizes.py"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def lua(v, ind=1):
    pad = "\t" * ind
    if isinstance(v, dict):
        items = [f'{pad}{k if k.isidentifier() else "[" + json.dumps(k) + "]"} = {lua(x, ind + 1)},'
                 for k, x in v.items() if not k.startswith("_")]
        return "{\n" + "\n".join(items) + "\n" + "\t" * (ind - 1) + "}"
    if isinstance(v, list):
        return "{ " + ", ".join(lua(x, ind + 1) for x in v) + " }"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return json.dumps(v)


def main():
    data = json.loads((ROOT / "standards" / "sizes.json").read_text(encoding="utf-8"))
    out = ROOT / "studio" / "StandardSizes.lua"
    out.parent.mkdir(exist_ok=True)
    out.write_text("--!strict\n-- GENERATED from standards/sizes.json by tools/gen_luau_sizes.py. Do not edit by hand.\n"
                   "-- All values in studs. " + data.get("_about", "").replace("\n", " ") + "\n"
                   "return " + lua(data) + "\n", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
