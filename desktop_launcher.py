from ksa_engine.__main__ import main
import sys


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("--editor")
    main()
