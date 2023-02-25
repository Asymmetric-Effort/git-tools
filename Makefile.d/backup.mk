git_tools/backup:
	@echo "$@ starting"
	@( \
		[[ ! -f ~/.bash_profile.bak ]] && \
			[[ -f ~/.bash_profile ]] && \
				cp ~/.bash_profile ~/.bash_profile.bak && \
					echo "done (bash)"; \
		[[ ! -f ~/.zshrc.bak ]] && \
			[[ -f ~/.zshrc ]] && \
				cp ~/.zshrc ~/.zshrc.bak && \
					echo "done (zsh)"; \
		echo "$@ done" \
	)