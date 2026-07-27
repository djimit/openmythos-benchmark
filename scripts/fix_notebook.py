import json

path = "/Users/dlandman/OpenMythos/openmythos-benchmark/notebooks/openmythos_r16_all_in_one.ipynb"

with open(path, "r") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell["source"])
        if "pip install" in source and "unsloth" in source:
            source = source.replace('"trl"', '"trl==0.15.2"')
            source = source.replace('"save_steps":100', '"save_steps":50')
            cell["source"] = [source]
            print("Fixed: pinned trl==0.15.2")
            break

with open(path, "w") as f:
    json.dump(nb, f, indent=1)

print("Notebook fixed!")
