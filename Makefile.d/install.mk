git_tools/install: git_tools/backup
	@echo "$@ starting '$$SHELL' ..."
	@( \
		[[ ! -d ~/git-tools ]] && mkdir -p ~/git-tools; \
		cp -rfvp src/ ~/git-tools/; \
		chmod +x ~/git-tools/*; \
		case "$${SHELL}" in \
		"/bin/bash") \
			echo "append path (bash)"; \
			sed -i -e '/export PATH="\$${PATH}:\$${HOME}\/git-tools\/"/d' ~/.bash_profile; \
			echo 'export PATH="$${PATH}:$${HOME}/git-tools/' >> ~/.bash_profile; \
			;; \
		"/bin/zsh") \
			echo "append path (zsh)"; \
			sed -i -e '/export PATH="\$${PATH}:\$${HOME}\/git-tools\/"/d' ~/.zshrc; \
			echo 'export PATH="$${PATH}:$${HOME}/git-tools/"' >> ~/.zshrc; \
			;; \
		"*") \
			echo "unsupported shell"; \
			exit 1; \
			;; \
		esac; \
		echo "$@ completed." \
	)

install: git_tools/install