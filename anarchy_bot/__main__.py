import asyncio
import sys
from main import main

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(' exiting ')
        sys.exit()

