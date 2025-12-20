all help test-system test-dev test-ifx test-all summary clean:
	@$(MAKE) -C pr $@

%:
	@$(MAKE) -C pr $@

.PHONY: all help test-system test-dev test-ifx test-all summary clean

