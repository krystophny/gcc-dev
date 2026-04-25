all help test-system test-dev test-ifx test-all summary clean:
	@$(MAKE) -C pr $@

provenance-check:
	@python3 scripts/check_testsuite_provenance.py --top 50

provenance-check-all:
	@python3 scripts/check_testsuite_provenance.py --include-testsuites --scope all --top 50

check-meta:
	@python3 scripts/gcc-workflow.py validate
	@bash scripts/check-status-docs.sh
	@python3 scripts/check-snapshot-freshness.py

install-hooks:
	@install -m 0755 scripts/hooks/pre-push .git/hooks/pre-push
	@echo "installed .git/hooks/pre-push"

clean-root:
	@find . -maxdepth 1 \( \
	    -name '*.o' -o -name '*.mod' -o -name '*.smod' -o \
	    -name '*.original' -o -name '*.earlydebug' -o -name '*.debug' \
	    -o -name '*.statistics' -o -name '*.profile_estimate' \
	    -o -name '*.s' -o -name '*.sum' -o -name '*.log' \
	    \) -type f -print -delete

.DEFAULT:
	@$(MAKE) -C pr $@

.PHONY: all help test-system test-dev test-ifx test-all summary \
	provenance-check provenance-check-all check-meta install-hooks \
	clean-root clean
