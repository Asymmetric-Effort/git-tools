git_tools/help:
	@echo '$@'
	@echo 'make git_tools/install   -> install the git-tools'
	@echo 'make git_tools/remove    -> uninstall the git-tools'
	@echo 'make git_tools/backup    -> backup the shell profiles (~/.bash_profile, ~/.zshrc)'
	@echo 'make git_tools/restore   -> restore the shell profiles (~/.bash_profile, ~/.zshrc)'
	@exit 0

include Makefile.d/*.mk
