def test_smoke():
    """
    A simple smoke test that checks if the main module can be imported.
    """
    try:
        import src.main
    except ImportError as e:
        assert False, f"Failed to import src.main: {e}"