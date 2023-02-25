Asymmetric-Effort/Bootstrap/Git-Tools
=====================================
(c) 2023 Sam Caldwell.  See LICENSE.txt

## Objective:
* To establish tools which can be installed to a local machine to
  interact smoothly with the git-server project.

## Tooling
* `make git_tools/install` -> installs the git tools
* `make git_tools/remove`  -> uninstalls the git tools

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
