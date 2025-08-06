import pathlib


def _get_configured_versions(repo_root: "pathlib.Path") -> "list[str]":
    python_versions = repo_root / ".python-version"
    result = []
    if python_versions.exists() and python_versions.is_file():
        with python_versions.open("r") as fp:
            result.extend(fp.readlines())

    return result


def configure_output() -> "dict":
    output: "dict" = {}
    config_dir = pathlib.Path(__file__).parent
    repo_root = config_dir.parent.parent.absolute()
    python_versions = _get_configured_versions(repo_root)
    for tpl in config_dir.glob("**/*.pytpl"):
        tpl_cfg: "dict" = {}
        tpl_cfg["output_files"] = {}
        for ver in python_versions:
            versions_parts = ver.split(".")
            if len(versions_parts) < 2:
                versions_parts.append("0")
            major, minor = (
                versions_parts[0], versions_parts[1])
            pyv: "str" = f"py{major}{minor}"
            tpl_without_ext = tpl.parent / tpl.stem
            target_file_relative: "str" = str(
                tpl_without_ext.relative_to(config_dir))
            target_file_relative = target_file_relative.replace("{pyv}", pyv)
            target_file_absolute = repo_root.joinpath(target_file_relative)
            tpl_cfg["output_files"][target_file_absolute] = {"variables": {
                "pythonVersion": f"{major}.{minor}"}
            }

        output[tpl.absolute()] = tpl_cfg

    return output
