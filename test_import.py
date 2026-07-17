try:
    from src.main_window import MainWindow
    print("Imports OK")
except Exception as e:
    import traceback
    traceback.print_exc()
