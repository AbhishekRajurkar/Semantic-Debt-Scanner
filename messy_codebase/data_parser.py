def parse_financial_data(data_string):
    # FLAW 10: Silent Error Handling. Catching a broad Exception and doing nothing, masking critical data corruption.
    try:
        data = data_string.split(",")
        return float(data[1])
    except Exception:
        pass