#
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2021-2023 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
""""""

from typing import Final, Optional, Protocol

# MyPy cannot resolve this during pull request
from pdm.project.config import ConfigItem as _ConfigItem  # type: ignore

from .actions.hook import CommitChanges, TagChanges
from .core.config import Config
from .plugin import BumpCommand as _Command


class _CoreLike(Protocol):
    """"""

    def register_command(
        self, command: type[_Command], name: Optional[str] = None
    ) -> None:
        """

        Parameters
        ----------
        command: type[_Command] :

        name: Optional[str] :
             (Default value = None)

        Returns
        -------

        """
        # Method empty: Only a protocol stub
        raise NotImplementedError()

    @staticmethod
    def add_config(name: str, config_item: _ConfigItem) -> None:
        """

        Parameters
        ----------
        name: str :

        config_item: _ConfigItem :


        Returns
        -------

        """
        # Method empty: Only a protocol stub
        raise NotImplementedError()


def main(core: _CoreLike) -> None:
    """

    Parameters
    ----------
    core: _CoreLike :


    Returns
    -------

    """
    core.register_command(_Command)

    config_prefix: Final[str] = Config.get_plugin_config_key_prefix()
    env_var_prefix: Final[str] = "PDM_BUMP_"

    core.add_config(
        f"{config_prefix}.commit_msg_tpl",
        _ConfigItem(
            "The default commit message. Uses templates 'from' and 'to'.",
            CommitChanges.default_commit_message,
        ),
    )
    core.add_config(
        f"{config_prefix}.perform_commit",
        _ConfigItem(
            "If set to true, commit the bumped changes automatically",
            CommitChanges.perform_commit,
        ),
    )
    core.add_config(
        f"{config_prefix}.auto_tag",
        _ConfigItem(
            "Create a tag after bumping and committing the changes",
            TagChanges.do_tag,
        ),
    )
    core.add_config(
        f"{config_prefix}.tag_add_prefix",
        _ConfigItem(
            "Adds the prefix v to the version tag",
            TagChanges.prepend_to_tag,
        ),
    )
    core.add_config(
        f"{config_prefix}.allow_dirty",
        _ConfigItem(
            "Allows tagging the project, if it is dirty",
            TagChanges.allow_dirty,
        ),
    )

    vcs_config_namespace: Final[str] = f"{config_prefix}.vcs"
    vcs_env_var_prefix: Final[str] = f"{env_var_prefix}_VCS"

    core.add_config(
        f"{vcs_config_namespace}.provider",
        _ConfigItem(
            "Configures the VCS Provider to use.",
            "git-cli",
            env_var=f"{vcs_env_var_prefix}_PROVIDER",
        ),
    )
