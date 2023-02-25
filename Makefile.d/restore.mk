git_tools/restore:
	@echo "$@ starting"
	@( \
		[[ -f ~/.bash_profile.bak ]] && \
			cat ~/.bash_profile.bak > ~/.bash_profile && \
				echo "done (bash)"; \
		[[ -f ~/.zshrc.bak ]] && \
			cat ~/.zshrc.bak > ~/.zshrc && \
				echo "done (zsh)"; \
		echo "$@ done" \
	)