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
EXIT_ERROR_LIST_SERVER_SPECIFIED = 21

EXIT_ERROR_GET_SERVER_BAD_INPUT = 10
EXIT_ERROR_GET_SERVER_EXCEPTION = 11
EXIT_ERROR_SET_SERVER_INVALID = 15
EXIT_ERROR_SET_SERVER_EXCEPTION = 16
EXIT_ERROR_LIST_REPOS_EXCEPTION = 20
EXIT_ERROR_CREATE_REPO_INVALID = 30
EXIT_ERROR_CREATE_REPO_EXCEPTION = 31
EXIT_ERROR_DELETE_REPO_INVALID = 40
EXIT_ERROR_DELETE_REPO_EXCEPTION = 41
EXIT_INTERNAL_ERROR_INVALID_CMD = 50

disallowed_git_servers = [
    'github.com',
    'bitbucket.com',
    'gitlabs.com'
    'visualstudio.com',
    'vsts.com',
]

CMD_CREATE = "create"
CMD_DELETE = "delete"
CMD_LIST = "list"
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

    @staticmethod
    def __valid_repo_name(repo: str) -> bool:
        """
            Determine if the input string is a valid repository name

            :param repo: str
            :return: bool
        """
        pattern = compile("^[a-zA-Z.-_/0-9]{1-32}$")
        return not (pattern.match(repo) is None)

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

    @staticmethod
    def runner(command: list) -> (int, str):
        """
            Execute a command and return the captured output.

            :param command: list
            :return: int(exit_code), str(stdout)
        """
        try:
            return EXIT_SUCCESS, str(run(command, shell=True, check=True, capture_output=True).stdout)
        except Exception as e:
            return EXIT_ERROR_LOCAL_GIT_COMMAND, f"{e}"

    def ssh_runner(self, server: str, command: str,
                   args: list = []) -> (int, str):
        """
            Execute an ssh command against the remote git server.

            :param server: str
            :param command: str
            :param args: list (default: [])
            :return: int(exit_code), str(stdout)
        """
        try:
            cmd = [f"ssh {server} {command}"]
            cmd.extend(args)
            return EXIT_SUCCESS, str(self.runner(cmd))
        except Exception as e:
            return EXIT_ERROR_SSH_GIT_COMMAND, f"{e}"

    def __get_server(self, this_scope: bool = False) -> (int, str):
        """
            return the preferred git server

            :param this_scope: bool
            :return: int(exit_code), str(stdout)
        """
        try:
            cmd = [f"git config",
                   f"{self.__global_flag(this_scope)}",
                   "--get git_tools.preferred_gitserver"]
            git_server = self.runner(cmd)
            if git_server == "":
                return EXIT_ERROR_GET_SERVER_BAD_INPUT, \
                    "git_tools.preferred_gitserver not defined." \
                    "Use 'git use <private_server>' first."
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
            if self.__valid_server_name(server_name):
                cmd = [f"git config",
                       f"{self.__global_flag(this_scope)}",
                       f"git_tools.preferred_gitserver '{server_name}'"]
                git_server = self.runner(cmd)
                return EXIT_SUCCESS, git_server
            else:
                return EXIT_ERROR_SET_SERVER_INVALID, \
                    f"{server_name} is invalid or is one of several " \
                    "disallowed git servers that cannot be used with Git Tools"
        except Exception as e:
            if this_scope:
                return EXIT_ERROR_SET_SERVER_EXCEPTION, f"(setting preferred server) {e}"
            else:
                return self.__set_server(server_name=server_name, this_scope=this_scope)

    def use(self, server_name: str,
            this_scope: bool = False) -> (int, str):
        """
            Configure the current preferred git server.

            :param server_name: str
            :param this_scope: bool (default False
            :return: int(exit_code), str(stdout)
        """
        return self.__set_server(server_name=server_name, this_scope=this_scope)

    def list_repositories(self, search_scope: bool = False) -> (int, str):
        """
            List the repositories in the preferred server (if set)

            :param search_scope: bool (default: false)
            :return: int (exit_code), str (list of repos)
        """
        try:
            exit_code, stdout = self.__get_server(search_scope)
            if exit_code != 0:
                return exit_code, stdout
            return self.ssh_runner(server=stdout, command=CMD_LIST)
        except Exception as e:
            return EXIT_ERROR_LIST_REPOS_EXCEPTION, \
                f"Error: could not list repositories. {e}"

    def create_repository(self, repo: str,
                          search_scope: bool = False) -> (int, str):
        """
            Create a new repository on the preferred server.

            :param repo: str
            :param search_scope: bool (default: false)
            :return: int (exit_code), str (list of repos)
        """
        stdout = "not_defined"
        try:
            exit_code, stdout = self.__get_server(search_scope)
            if exit_code != 0:
                return exit_code, stdout
            if self.__valid_repo_name(repo):
                return self.ssh_runner(stdout, CMD_CREATE, [repo])
            else:
                return EXIT_ERROR_CREATE_REPO_INVALID, f"{repo} is not valid"
        except Exception as e:
            return EXIT_ERROR_CREATE_REPO_EXCEPTION, \
                f"could not create repository ({repo}) on {stdout}. {e}"

    def delete_repository(self, repo: str,
                          search_scope: bool = False) -> (int, str):
        """
            Delete a new repository on the preferred server.

            :param repo: str
            :param search_scope: bool (default: false)
            :return: int (exit_code), str (list of repos)
        """
        stdout = "not_defined"
        try:
            exit_code, stdout = self.__get_server(search_scope)
            if exit_code != 0:
                return exit_code, stdout
            if self.__valid_repo_name(repo):
                return self.ssh_runner(stdout, CMD_DELETE, [repo])
            else:
                return EXIT_ERROR_DELETE_REPO_INVALID, f"{repo} is not valid"
        except Exception as e:
            return EXIT_ERROR_DELETE_REPO_EXCEPTION, \
                "Error: could not delete repository " \
                f"({repo}) on {stdout}. {e}"


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
            CMD_USE,
            CMD_LIST,
            CMD_CREATE,
            CMD_DELETE
        ],
        help="Git Tools Command")

    parser.add_argument(
        "--repo",
        type=str,
        required=False,
        default="",
        help="specify a repository name")

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

    return parser.parse_args()


def show_usage(error: str, exit_code: int = 255) -> int:
    """
        Show the program usage on error.

        :param error: str
        :param exit_code: int (default: 255)
        :return: int
    """
    print(f"Error: {error}\n\n{help_text}\n")
    return exit_code


def main() -> int:
    """
        main program for executing commandline.

        :return: int (exit code)
    """
    git = GitServer()
    args = get_args()

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
        git.use(server_name=args.server, this_scope=args.scope)

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
            return git.create_repository(repo=args.repo,
                                         search_scope=args.scope)
        else:
            return git.delete_repository(repo=args.repo,
                                         search_scope=args.scope)
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
    else:
        return show_usage("Internal programming error (command: "
                          f"{args.command})",
                          EXIT_INTERNAL_ERROR_INVALID_CMD)


if __name__ == "__main__":
    exit(main())
