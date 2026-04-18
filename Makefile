all help test-system test-dev test-ifx test-all summary clean:
	@$(MAKE) -C pr $@

provenance-check:
	@python3 scripts/check_testsuite_provenance.py --top 50

.DEFAULT:
	@$(MAKE) -C pr $@

.PHONY: all help test-system test-dev test-ifx test-all summary provenance-check clean
