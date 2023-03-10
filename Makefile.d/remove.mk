git_tools/remove:
	@echo "$@ starting..."
	@( \
		[[ ! -d ~/git-tools ]] && rm -rf ~/git-tools; \
		case "$${SHELL}" in \
		"/bin/bash") \
			echo "remove git-tools from path (bash)"; \
			sed -i -e '/export PATH="\$${PATH}:\$${HOME}\/git-tools\/"/d' ~/.bash_profile; \
			git config --unset core.preferredGitserver || true; \
			git config --global --unset core.preferredGitserver || true; \
			;; \
		"/bin/zsh") \
			echo "remove git-tools from path (zsh)"; \
			sed -i -e '/export PATH="\$${PATH}:\$${HOME}\/git-tools\/"/d' ~/.zshrc; \
			;; \
		"*") \
			exit 1; \
			;; \
		esac; \
		echo "$@ complete" \
	)
