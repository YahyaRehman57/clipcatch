from pathlib import Path



def build_directory_tree(path: Path):
    tree = {}
    for item in path.iterdir():
        if item.is_dir():
            tree[item.name] = build_directory_tree(item)
        else:
            tree.setdefault("files", []).append(item.name)
    return tree