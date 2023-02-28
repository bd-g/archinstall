import archinstall

import logging
import shlex

from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL


class DirPicker:
    def pick():
        # TODO duplicating fzf instructions here is not ideal, can easily grow stale
        filter_instructions = (
            'echo "'
            "Select directory (or directories) for configuration(s) to be saved in\n\n"
            "* Type to filter options\n"
            "* Use arrow keys to navigate save directory options\n"
            "    * Alternates: Mouse scroll/click, Ctrl-K/Ctrl-J, Ctrl-P/Ctrl-N\n"
            "* Single selection:\n"
            "    * Press ENTER to proceed with highlighted directory\n"
            "* Multi selection:\n"
            "    * Press TAB to select a directory for saving (you can select multiple directories)\n"
            "    * Press ENTER when finished\n"
            '* Press ESC/Ctrl-C/Ctrl-G to exit without making a selection"'
        )
        filter_process = Popen(
            shlex.split(
                f"fzf --multi --print0 --preview-window 'left:wrap,50%,border-right' --keep-right --preview"
            )
            + [filter_instructions],
            stdin=PIPE,
            stdout=PIPE,
        )

        dirs_to_exclude = [
            "/bin",
            "/dev",
            "/lib",
            "/lib64",
            "/lost+found",
            "/opt",
            "/proc",
            "/run",
            "/sbin",
            "/srv",
            "/sys",
            "/usr",
            "/var",
            "/test",
        ]
        find_exclude = (
            "-path " + " -prune -o -path ".join(dirs_to_exclude) + " -prune -o "
        )
        file_picker_command = f"find / -type d {find_exclude} -print"
        find_process = Popen(
            shlex.split(file_picker_command),
            stdout=filter_process.stdin,
            stderr=DEVNULL,
        )
        archinstall.log(
            "When picking a directory to save configuration files to,"
            " by default we will ignore the following folders: "
            + ",".join(dirs_to_exclude)
        )

        filter_stdout, filter_stderr = filter_process.communicate()
        # Once selection is picked, no need to continue finding directories in the background
        find_process.kill()
        match filter_process.returncode:
            case 0:
                # Normal exit
                pass
            case 1:
                # No match
                pass
            case 2:
                # Error within fzf
                archinstall.log(
                    f"fzf internal error: {filter_stderr}",
                    level=logging.ERROR,
                )
                raise ValueError(
                    "find/fzf command to select a save directory failed", filter_stderr
                )
            case 130:
                # Interrupted with ESC/Ctrl-C/Ctrl-G
                pass

        selections = list(filter(None, filter_stdout.decode("UTF-8").split("\x00")))
        return selections
