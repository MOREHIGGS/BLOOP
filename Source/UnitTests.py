if __name__ == "__main__":
    # These imports are used despite what ruff thinks
    from PythoniseMathematica import PythoniseMathematicaUnitTests # noqa: F401
    from ParsedExpression import ParsedExpressionUnitTests # noqa: F401
    from TrackVEV import TrackVEVUnitTests # noqa: F401
    from Z2_ThreeHiggsBmGenerator import BmGeneratorUnitTests # noqa: F401
    from PDGData import PDGUnitTests # noqa: F401

    from unittest import main

    main()
