git-tools/lint/python:
	@flake8 src/git_server.py
	@echo "$@ done."

git-tools/lint/shell:
	@shellcheck src/git-*
	@echo "$@ done."

git_tools/lint: git-tools/lint/python git-tools/lint/shell
	@echo "$@ done."

lint: git_tools/lint


