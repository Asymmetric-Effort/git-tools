#!/usr/bin/env python3
from argparse import ArgumentParser
from argparse import Namespace
from re import compile
from subprocess import run

EXIT_SUCCESS = 0
EXIT_ERROR_LOCAL_GIT_COMMAND = 1
EXIT_ERROR_SSH_GIT_COMMAND = 2

EXIT_ERROR_ARG_USE_SERVER_MISSING = 10
EXIT_ERROR_ARG_USE_REPO_SPECIFIED = 11
EXIT_ERROR_CRDEL_REPO_MISSING = 14
EXIT_ERROR_CRDEL_SERVER_SPECIFIED = 15

EXIT_ERROR_LIST_REPO_SPECIFIED = 20
EXIT_ERROR_LIST_SERVER_SPECIFIED = 25

EXIT_ERROR_GET_SERVER_BAD_INPUT = 30
EXIT_ERROR_GET_SERVER_EXCEPTION = 35

EXIT_ERROR_SET_SERVER_INVALID = 40
EXIT_ERROR_SET_SERVER_EXCEPTION = 45

EXIT_ERROR_LIST_REPOS_EXCEPTION = 50

EXIT_ERROR_CREATE_REPO_INVALID = 60
EXIT_ERROR_CREATE_REPO_EXCEPTION = 65

EXIT_ERROR_DELETE_REPO_INVALID = 70
EXIT_ERROR_DELETE_REPO_EXCEPTION = 75

EXIT_ERROR_ARG_USE_SERVER_SPECIFIED = 80
EXIT_ERROR_ARG_RENAME_SRC_REPO_MISSING = 82
EXIT_ERROR_ARG_RENAME_DEST_REPO_MISSING = 85

EXIT_INTERNAL_ERROR_INVALID_CMD = 200

disallowed_git_servers = [
    'github.com',
    'bitbucket.com',
    'gitlabs.com'
    'visualstudio.com',
    'vsts.com',
]

PREFERRED_SERVER_KEY = "core.preferredGitserver"

CMD_CREATE = "create"
CMD_DELETE = "delete"
CMD_LIST = "list"
CMD_RENAME = "rename"
CMD_USE = "use"

help_text = """
Usage:
    git create <repo>
    git delete <repo>
    git list 
    git use <server>
"""


class GitServer(object):
    """
        Class for Interacting with Git (local and remote)
    """

    def __init__(self, debug: bool = False) -> None:
        """
            class constructor

            :param debug: bool
            :return: None
        """
        self.__debug = debug

    def debug(self, msg: str) -> None:
        """
            print debug messages

            :param msg: str
            :return: None
        """
        if self.__debug:
            print(f"[DEBUG]: {msg}")

    @staticmethod
    def __valid_server_name(server_name: str) -> bool:
        """
            return whether the server_name is valid
            and not disallowed.

            :param server_name: str
            :return: bool
        """
        # ToDo: validate name against a regex
        for disallowed_server in disallowed_git_servers:
            if disallowed_server in server_name:
                return False
        return True

    def __valid_repo_name(self, repo: str) -> bool:
        """
            Determine if the input string is a valid repository name

            :param repo: str
            :return: bool
        """
        self.debug(f"Validating repo '{repo}'")
        pattern = compile("^[a-zA-Z][a-zA-Z./-_/0-9]+[a-zA-Z0-9]$")
        self.debug(f"Valid? {pattern.match(repo)}")
        return pattern.match(repo) is not None

    @staticmethod
    def __global_flag(global_scope: bool) -> str:
        """
            return the --global flag if s is true.

            :param global_scope: bool
            :return: str
        """
        if global_scope:
            return "--global"
        else:
            return ""

    def runner(self, command: str) -> (int, str):
        """
            Execute a command and return the captured output.

            :param command: str
            :return: int(exit_code), str(stdout)
        """
        try:
            self.debug(f"command(runner): {command}")
            result = run(command,
                         shell=True,
                         check=False,
                         capture_output=True)
            return result.returncode, result.stdout.decode().strip()
        except Exception as e:
            return EXIT_ERROR_LOCAL_GIT_COMMAND, f"{e}"

    def ssh_runner(self,
                   server: str,
                   command: str) -> (int, str):
        """
            Execute an ssh command against the remote git server.

            :param server: str
            :param command: str
            :return: int(exit_code), str(stdout)
        """
        try:
            cmd = f"ssh -o 'StrictHostKeyChecking no' " + \
                  f"git@{server} {command}"
            self.debug(f"command(ssh_runner): {cmd}")
            return self.runner(cmd)
        except Exception as e:
            return EXIT_ERROR_SSH_GIT_COMMAND, f"{e}"

    def __get_server(self, this_scope: bool = False) -> (int, str):
        """
            return the preferred git server

            :param this_scope: bool
            :return: int(exit_code), str(stdout)
        """
        try:
            cmd = "git config " + \
                  f"{self.__global_flag(this_scope).strip()} " + \
                  f"--get {PREFERRED_SERVER_KEY}"
            exit_code, git_server = self.runner(cmd)
            self.debug(f"git_server[{exit_code}]:'{git_server}'")
            if (exit_code != 0) or (git_server == ""):
                return EXIT_ERROR_GET_SERVER_BAD_INPUT, \
                    f"{PREFERRED_SERVER_KEY} not defined." \
                    f"Use 'git {CMD_USE} <private_server>' first."
            else:
                return EXIT_SUCCESS, git_server
        except Exception as e:
            if this_scope:
                return EXIT_ERROR_GET_SERVER_EXCEPTION, \
                    f"(getting preferred server) {e}"
            else:
                # Retry with global scope because we were not
                # in a git repository we could configure locally.
                return self.__get_server(this_scope=True)

    def __set_server(self, server_name: str,
                     this_scope: bool = False) -> (int, str):
        """
            set the preferred git server

            :param server_name: str
            :param this_scope: bool
            :return: int(exit_code), str(stdout)
        """
        try:
            self.debug(f"setting preferred server:'{server_name}'")
            if self.__valid_server_name(server_name):
                cmd = "git config " + \
                      f"{self.__global_flag(this_scope)} " + \
                      f"{PREFERRED_SERVER_KEY} " + \
                      f"{server_name}"
                exit_code, stdout = self.runner(cmd)
                if exit_code != 0:
                    if this_scope:
                        return exit_code, stdout
                    else:
                        return self.__set_server(server_name=server_name, this_scope=True)
                else:
                    return exit_code, stdout

            else:
                return EXIT_ERROR_SET_SERVER_INVALID, \
                    f"{server_name} is invalid or is one of several " \
                    "disallowed git servers that cannot be used with Git Tools"
        except Exception as e:
            if this_scope:
                return EXIT_ERROR_SET_SERVER_EXCEPTION, f"(setting preferred server) {e}"
            else:
                self.debug("escalating scope")
                return self.__set_server(server_name=server_name, this_scope=True)

    def create_repository(self, repo: str,
                          search_scope: bool = False) -> (int, str):
        """
            Create a new repository on the preferred server.

            :param repo: str
            :param search_scope: bool (default: false)
            :return: int (exit_code), str (list of repos)
        """
        server = ""
        try:
            self.debug(f"Get Preferred server to create '{repo}'")
            exit_code, stdout = self.__get_server(search_scope)
            if exit_code == 0:
                self.debug(f"Preferred server found for create '{repo}'")
            else:
                self.debug(f"could not find preferred server"
                           f"[{exit_code}]: '{stdout}'")
                return exit_code, stdout
            server = stdout
            self.debug(f"Validate repo name ({repo}) "
                       f"for create on '{server}'")
            if self.__valid_repo_name(repo):
                self.debug(f"repo name is valid: '{repo}'")
                cmd = f"create {repo}"
                return self.ssh_runner(server=server, command=cmd)
            else:
                self.debug(f"repo name is not valid: '{repo}'")
                return EXIT_ERROR_CREATE_REPO_INVALID, f"{repo} is not valid"
        except Exception as e:
            return EXIT_ERROR_CREATE_REPO_EXCEPTION, \
                f"could not create repository ({repo}) on '{server}'. {e}"

    def delete_repository(self, repo: str,
                          search_scope: bool = False) -> (int, str):
        """
            Delete a new repository on the preferred server.

            :param repo: str
            :param search_scope: bool (default: false)
            :return: int (exit_code), str (list of repos)
        """
        server = ""
        try:
            self.debug(f"Get Preferred server to delete '{repo}'")
            exit_code, stdout = self.__get_server(search_scope)
            if exit_code == 0:
                self.debug(f"Preferred server found for delete '{repo}'")
            else:
                self.debug(f"could not find preferred server"
                           f"[{exit_code}]: '{stdout}'")
                return exit_code, stdout
            server = stdout
            self.debug(f"Validate repo name ({repo}) "
                       f"for delete on '{server}'")
            if self.__valid_repo_name(repo):
                self.debug(f"repo name is valid: '{repo}'")
                cmd = f"delete {repo}"
                return self.ssh_runner(server=server, command=cmd)
            else:
                self.debug(f"repo name is not valid: '{repo}'")
                return EXIT_ERROR_DELETE_REPO_INVALID, f"{repo} is not valid"
        except Exception as e:
            return EXIT_ERROR_DELETE_REPO_EXCEPTION, \
                f"could not delete repository ({repo}) on '{server}'. {e}"

    def list_repositories(self, search_scope: bool = False) -> (int, str):
        """
            List the repositories in the preferred server (if set)

            :param search_scope: bool (default: false)
            :return: int (exit_code), str (list of repos)
        """
        try:
            exit_code, stdout = self.__get_server(search_scope)
            if exit_code != 0:
                return exit_code, f"(list): {stdout}"
            server = stdout
            exit_code, stdout = self.ssh_runner(server=server, command=CMD_LIST)
            if exit_code == 0:
                repo_list = ""
                header = "repositories on {server}"
                base_path = "/git/repos/"
                name_width = 0
                path_width = 0
                repos = {}
                for name in stdout.split('\n'):
                    path = f"{base_path}{name}"
                    repos[name] = {
                        "name": name + " " * (name_width - len(name)),
                        "path": path + " " * (path_width - len(path)),
                    }
                    if len(name) > name_width:
                        name_width = len(name)
                    if len(repos[name]["path"]) > path_width:
                        path_width = len(repos[name]["path"])
                width = len(header)
                repo_list = ""

                for name, value in repos.items():
                    line = f"| {value['name']} | {value['path']} |"
                    if len(line) > width:
                        width = len(line)
                    repo_list += line + "\n"

                self.debug(f"width: {width}")
                header = "|" + header + " " * (width - len(header) - 2) + "|\n"
                separator = "+" + "-" * (width - 2) + "+\n"
                return exit_code, f"{separator}" \
                                  f"{header}" \
                                  f"{separator}" \
                                  f"{repo_list}" \
                                  f"{separator}"
            else:
                return exit_code, stdout
        except Exception as e:
            return EXIT_ERROR_LIST_REPOS_EXCEPTION, \
                f"Error: could not list repositories. {e}"

    def rename(self, source_repo: str, destination_repo: str,
               search_scope: bool = False) -> (int, str):
        """
            Move/rename a source_repo to a destination repo within
            a given search_scope.

            :param source_repo: str
            :param destination_repo: str
            :param search_scope: bool
            :return: int (exit_code), str (list of repos)
        """
        try:
            exit_code, stdout = self.__get_server(search_scope)
            if exit_code != 0:
                return exit_code, stdout
            server = stdout
            cmd = f"rename {source_repo} {destination_repo}"
            return self.ssh_runner(server=server, command=cmd)
        except Exception as e:
            return EXIT_ERROR_LIST_REPOS_EXCEPTION, \
                f"Error: could not move/rename repository. " \
                f"{source_repo} to {destination_repo} " \
                f"error: {e}"

    def use(self, server_name: str,
            this_scope: bool = False) -> (int, str):
        """
            Configure the current preferred git server.

            :param server_name: str
            :param this_scope: bool (default False
            :return: int(exit_code), str(stdout)
        """
        exit_code, stdout = self.__set_server(server_name=server_name,
                                              this_scope=this_scope)
        if exit_code == 0:
            return exit_code, \
                f"Set preferred server ('{server_name}'): ok"
        else:
            return exit_code, \
                f"Set preferred server ('{server_name}'): failed"


def get_args() -> Namespace:
    """
        get commandline arguments

        :return: Namespace
    """
    parser = ArgumentParser(description="Git Tools CommandLine")
    parser.add_argument(
        "--command",
        type=str,
        required=True,
        choices=[
            CMD_CREATE,
            CMD_DELETE,
            CMD_LIST,
            CMD_RENAME,
            CMD_USE
        ],
        help="Git Tools Command")

    parser.add_argument(
        "--repo",
        type=str,
        required=False,
        default="",
        help="specify a repository name")

    parser.add_argument(
        "--source",
        type=str,
        required=False,
        default="",
        help="specify a source repository name"
    )

    parser.add_argument(
        "--destination",
        type=str,
        required=False,
        default="",
        help="specify a destination repository name"
    )

    parser.add_argument(
        "--server",
        type=str,
        required=False,
        default="",
        help="specify a git server")

    parser.add_argument(
        "--global",
        dest="scope",
        required=False,
        action="store_true",
        default=False,
        help="search global or local .gitconfig")

    parser.add_argument(
        "--debug",
        required=False,
        default=False,
        action="store_true",
        help="enable debug messages"
    )

    return parser.parse_args()


def show_usage(error: str, exit_code: int = 255) -> int:
    """
        Show the program usage on error.

        :param error: str
        :param exit_code: int (default: 255)
        :return: int
    """
    if error.strip() == "":
        error = "unspecified"
    print(f"Error: '{error}'\n\n{help_text}\n")
    return exit_code


def main() -> int:
    """
        main program for executing commandline.

        :return: int (exit code)
    """
    args = get_args()
    git = GitServer(args.debug)

    if args.command in [CMD_USE]:
        """
            git use <server>
                -- define the preferred git server for the specified scope
                -- where scope is not defined, local scope will be used if
                   the current directory is a git repo.
                -- if no scope is defined in the current directory, scope 
                   will fall back to global scope.
        """
        if args.server.strip() == "":
            return show_usage("preferred server not specified for "
                              f"{args.command}.",
                              EXIT_ERROR_ARG_USE_SERVER_MISSING)

        if args.repo.strip() != "":
            return show_usage("repo should not be specified for "
                              f"{args.command}",
                              EXIT_ERROR_ARG_USE_REPO_SPECIFIED)

        exit_code, stdout = git.use(server_name=args.server, this_scope=args.scope)

        if exit_code == 0:
            print(stdout)
            return exit_code
        else:
            return show_usage(stdout, exit_code)

    elif args.command in [CMD_CREATE, CMD_DELETE]:
        """
            get create <repo>
            get delete <repo>
                -- create or delete a repository on the preferred git server,
                   where scope is defined or where the preferred git server
                   lists repositories on a locally defined server and if not
                   defined it will list the repositories on the globally
                   defined preferred server.
        """
        if args.repo.strip() == "":
            return show_usage(f"repo not specified for {args.command}.",
                              EXIT_ERROR_CRDEL_REPO_MISSING)

        if args.server.strip() != "":
            return show_usage("preferred server should not be specified for "
                              f"{args.command}",
                              EXIT_ERROR_CRDEL_SERVER_SPECIFIED)

        if args.command == CMD_CREATE:
            exit_code, stdout = git.create_repository(repo=args.repo,
                                                      search_scope=args.scope)
        else:
            exit_code, stdout = git.delete_repository(repo=args.repo,
                                                      search_scope=args.scope)
        if exit_code == 0:
            print("OK")
            return 0
        else:
            return show_usage(stdout, exit_code)

    elif args.command in [CMD_LIST]:
        """
            git list
                -- list the repositories on the preferred git server, where 
                   scope is defined or where the preferred git server lists
                   repositories on a locally defined server and if not
                   defined it will list the repositories on the globally
                   defined preferred server.
        """
        if args.repo.strip() != "":
            return show_usage("repo should not be specified for "
                              f"{args.command}",
                              EXIT_ERROR_LIST_REPO_SPECIFIED)
        if args.server.strip() != "":
            return show_usage("preferred server should not be specified for "
                              f"{args.command}",
                              EXIT_ERROR_LIST_SERVER_SPECIFIED)
        exit_code, text = git.list_repositories(args.scope)
        if exit_code != 0:
            return show_usage(text, exit_code)
        else:
            print(text)
            return exit_code

    elif args.command in [CMD_RENAME]:
        """
            get rename <source_repo> <destination_repo>
                -- rename/move a source_repo to the destination_repo.
                -- create or delete a repository on the preferred git server,
                   where scope is defined or where the preferred git server
                   lists repositories on a locally defined server and if not
                   defined it will list the repositories on the globally
                   defined preferred server.
        """
        if args.server.strip() != "":
            return show_usage("server should not be specified for "
                              f"{args.command}.",
                              EXIT_ERROR_ARG_USE_SERVER_MISSING)

        if args.source.strip() == "":
            return show_usage("source should be specified for "
                              f"{args.command}",
                              EXIT_ERROR_ARG_RENAME_SRC_REPO_MISSING)

        if args.destination.strip() == "":
            return show_usage("destination should be specified for "
                              f"{args.command}",
                              EXIT_ERROR_ARG_RENAME_DEST_REPO_MISSING)

        exit_code, stdout = git.rename(
            source_repo=args.source.strip(),
            destination_repo=args.destination.strip(),
            search_scope=args.scope)

        if exit_code != 0:
            return show_usage(stdout, exit_code)
        return exit_code
    else:
        return show_usage("Internal programming error "
                          f"(command: {args.command})",
                          EXIT_INTERNAL_ERROR_INVALID_CMD)


if __name__ == "__main__":
    exit(main())
