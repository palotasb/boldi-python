from pathlib import Path

from hatch_vcs.version_source import VCSVersionSource
from hatchling.metadata.plugin.interface import MetadataHookInterface
from packaging.requirements import Requirement


def update_internal_dependencies(dependencies: list[str], version: str):
    for i, dependency in enumerate(dependencies):
        requirement = Requirement(dependency)
        if requirement.name.startswith("boldi"):
            requirement.specifier &= f"=={version}"
            dependencies[i] = str(requirement)


class CustomMetadataHook(MetadataHookInterface):
    def __init__(self, root: str, config: dict) -> None:
        super().__init__(root, config)

    def update(self, metadata: dict) -> None:
        version_source = VCSVersionSource(root=Path(self.root).parent.parent.resolve().__str__(), config={})
        version = version_source.get_version_data()["version"]
        print(version)
        update_internal_dependencies(metadata.get("dependencies", []), version)
