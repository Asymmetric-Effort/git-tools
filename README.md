Asymmetric-Effort/Bootstrap/Git-Tools
=====================================
(c) 2023 Sam Caldwell.  See LICENSE.txt

## Objective:
  * To establish tools which can be installed to a local machine to
    interact smoothly with the git-server project.

## Installing/Removing `git-tools`...
### To Install...
  Execute `make git_tools/install`
  > Note: you must run `source ~/.zshrc` or open a new terminal.

### To Remove...
  Execute `make git_tools/remove`


## Commands in the Toolkit
### `git use <git server>`
  * Set the preferred git server (local config if inside a current repo)
  * If the current directory is not a local repository, set global config.

### `git create <repo>`
  * Create a repository on the current preferred server.

### `git delete <repo>`
  * Delete a repository on the current preferred server.

### `git list`
  * List the repositories on the current preferred server.


## "Preferred Server" Configuration
The git-tools project is designed to work with local `git-server` instances
and to provide tooling that makes git operations easy.

These `git-server` instances are referred to as "preferred server" instances,
and each can be defined specific to a local git repo or globally to the host
through the `git use <server>` command.

If the user calls `git use <server>` from within the directory of a local
git repository, then `git use <server>` will configure the "preferred server"
of the specific repository (e.g. `<repo_dir>/.git/config`).

However, if the user calls the `git user <server>` command from any directory
which is not initialized as a git repository, the command will configure the
"preferred server" in the global git config (e.g. `~/.gitconfig`).

This configuration will be stored as:

```
[git_tools]
     preferred_gitserver = 'server.fqdn.tld' 
```

This change is effected through the following command, wrapped by the
python3 tooling:

  `git config [--global] git_tools.preferred_gitserver 'server.fqdn.tld'`
