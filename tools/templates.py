import importlib
import pathlib
import string
import sys


path = pathlib.Path(__file__).parent
repo_root = path.parent

tpl_cfg = repo_root / ".config" / "templates"

sys.path = [str(tpl_cfg)] + sys.path

configure = importlib.import_module("configure")

config: "dict" = {}
if hasattr(configure, "configure_output"):
    inner_config = configure.configure_output()
    if isinstance(inner_config, dict):
        config.update(inner_config)

for template in config:
    tpl_out = config[template]["output_files"]
    template_text = template.read_text()
    transform = string.Template(template_text)
    for target in tpl_out:
        variables = tpl_out[target]["variables"]
        text = transform.substitute(variables)
        target_dir = target.parent
        target_dir.mkdir(exist_ok=True, parents=True)
        target.write_text(text)
